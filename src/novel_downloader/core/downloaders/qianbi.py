#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.qianbi
----------------------------------------

Downloader implementation for Qianbi novels, with chapter ID repair logic.
"""

import asyncio
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from novel_downloader.core.downloaders.base import BaseDownloader
from novel_downloader.core.downloaders.registry import register_downloader
from novel_downloader.core.downloaders.signals import (
    STOP,
    Progress,
    StopToken,
)
from novel_downloader.core.interfaces import (
    FetcherProtocol,
    ParserProtocol,
)
from novel_downloader.models import (
    BookConfig,
    BookInfoDict,
    ChapterDict,
    DownloaderConfig,
)
from novel_downloader.utils import (
    ChapterStorage,
    async_jitter_sleep,
)


@register_downloader(site_keys=["qianbi"])
class QianbiDownloader(BaseDownloader):
    """
    Downloader for Qianbi (铅笔) novels.

    Repairs missing chapter IDs by following 'next' links, then downloads
    each chapter as a unit (fetch -> parse -> enqueue storage).
    """

    DEFAULT_SOURCE_ID = 0

    def __init__(
        self,
        fetcher: FetcherProtocol,
        parser: ParserProtocol,
        config: DownloaderConfig,
    ):
        super().__init__(fetcher, parser, config, "qianbi")

    async def _download_one(
        self,
        book: BookConfig,
        *,
        progress_hook: Callable[[int, int], Awaitable[None]] | None = None,
        cancel_event: asyncio.Event | None = None,
        **kwargs: Any,
    ) -> None:
        """
        The full download logic for a single book.

        :param book: BookConfig with at least 'book_id'.
        """
        TAG = "[Downloader]"

        book_id = book["book_id"]
        start_id = book.get("start_id")
        end_id = book.get("end_id")
        ignore_set = set(book.get("ignore_ids", []))

        raw_base = self._raw_data_dir / book_id
        raw_base.mkdir(parents=True, exist_ok=True)
        html_dir = self._debug_dir / book_id / "html"

        chapter_storage = ChapterStorage(
            raw_base=raw_base,
            priorities=self.PRIORITIES_MAP,
        )
        chapter_storage.connect()

        def cancelled() -> bool:
            return bool(cancel_event and cancel_event.is_set())

        try:
            # --- metadata ---
            book_info = await self.load_book_info(book_id=book_id, html_dir=html_dir)
            if not book_info:
                return

            book_info = await self._repair_chapter_ids(
                book_id,
                book_info,
                chapter_storage,
                html_dir,
            )

            vols = book_info["volumes"]
            total_chapters = sum(len(v["chapters"]) for v in vols)
            if total_chapters == 0:
                self.logger.warning("%s 书籍没有章节可下载: %s", TAG, book_id)
                return

            progress = Progress(total_chapters, progress_hook)

            # --- queues & batching ---
            cid_q: asyncio.Queue[str | StopToken] = asyncio.Queue()
            save_q: asyncio.Queue[ChapterDict | StopToken] = asyncio.Queue()
            batch: list[ChapterDict] = []

            async def flush_batch() -> None:
                if not batch:
                    return
                try:
                    chapter_storage.upsert_chapters(batch, self.DEFAULT_SOURCE_ID)
                except Exception as e:
                    self.logger.error(
                        "[Storage] batch upsert failed (size=%d): %s",
                        len(batch),
                        e,
                        exc_info=True,
                    )
                else:
                    await progress.bump(len(batch))
                finally:
                    batch.clear()

            # --- stage: storage worker ---
            async def storage_worker() -> None:
                """
                Consumes parsed chapters, writes in batches.

                Terminates after receiving STOP from each chapter worker.

                On cancel: keeps consuming (to avoid blocking producers),
                flushes, and exits once all STOPs are seen.
                """
                stop_count = 0
                while True:
                    item = await save_q.get()
                    if isinstance(item, StopToken):
                        stop_count += 1
                        if stop_count == self.workers:
                            # All chapter workers have exited.
                            await flush_batch()
                            return
                        # else keep waiting for remaining STOPs
                        continue

                    # Normal chapter
                    batch.append(item)
                    if len(batch) >= self.storage_batch_size:
                        await flush_batch()

                    if cancelled():
                        # Drain whatever is already in the queue
                        try:
                            while True:
                                nxt = save_q.get_nowait()
                                if isinstance(nxt, StopToken):
                                    stop_count += 1
                                else:
                                    batch.append(nxt)
                        except asyncio.QueueEmpty:
                            pass
                        # Final flush of everything
                        await flush_batch()
                        # Wait for remaining STOPs so chapter workers can finish.
                        while stop_count < self.workers:
                            nxt = await save_q.get()
                            if isinstance(nxt, StopToken):
                                stop_count += 1
                        return

            # --- stage: chapter worker ---
            sem = asyncio.Semaphore(self.workers)

            async def chapter_worker() -> None:
                """
                Fetch + parse with retry, then enqueue to save_q.

                Exits on STOP, or early if cancel is set before starting a new fetch.
                """
                while True:
                    cid = await cid_q.get()
                    if isinstance(cid, StopToken):
                        # Propagate one STOP to storage and exit.
                        await save_q.put(STOP)
                        return

                    if not cid or cid in ignore_set:
                        # Ignore silently and continue.
                        continue

                    # If cancelled, don't start a new network call; let storage finish.
                    if cancelled():
                        await save_q.put(STOP)
                        return

                    async with sem:
                        chap = await self._process_chapter(book_id, cid, html_dir)
                    if chap:
                        await save_q.put(chap)

                    # polite pacing
                    await async_jitter_sleep(
                        self.request_interval,
                        mul_spread=1.1,
                        max_sleep=self.request_interval + 2,
                    )

            # --- stage: producer ---
            async def producer() -> None:
                """
                Enqueue chapter IDs (respecting start/end/skip_existing).
                Always sends STOP x workers at the end (even if cancelled early),
                so chapter workers can exit deterministically.
                """
                try:
                    async for cid in self._chapter_ids(vols, start_id, end_id):
                        if cancelled():
                            break
                        if self.skip_existing and chapter_storage.exists(cid):
                            # Count as completed but don't enqueue.
                            await progress.bump(1)
                        else:
                            await cid_q.put(cid)
                finally:
                    for _ in range(self.workers):
                        await cid_q.put(STOP)

            # --- run the pipeline ---
            async with asyncio.TaskGroup() as tg:
                tg.create_task(storage_worker())
                for _ in range(self.workers):
                    tg.create_task(chapter_worker())
                tg.create_task(producer())

            # --- done ---
            if cancelled():
                self.logger.info(
                    "%s Novel '%s' cancelled: flushed %d/%d chapters.",
                    TAG,
                    book_info.get("book_name", "unknown"),
                    progress.done,
                    progress.total,
                )
            else:
                self.logger.info(
                    "%s Novel '%s' download completed.",
                    TAG,
                    book_info.get("book_name", "unknown"),
                )

        finally:
            chapter_storage.close()

    async def _repair_chapter_ids(
        self,
        book_id: str,
        book_info: BookInfoDict,
        storage: ChapterStorage,
        html_dir: Path,
    ) -> BookInfoDict:
        """
        Fill in missing chapterId fields by retrieving the previous chapter
        and following its 'next_chapter_id'. Uses storage to avoid refetching.
        """
        prev_cid: str = ""
        for vol in book_info["volumes"]:
            for chap in vol["chapters"]:
                cid = chap.get("chapterId")
                if cid:
                    prev_cid = cid
                    continue

                # no valid previous to follow
                if not prev_cid:
                    continue

                # missing id: try storage
                data = storage.get_best_chapter(prev_cid)
                if not data:
                    # fetch+parse previous to discover next
                    data = await self._process_chapter(book_id, prev_cid, html_dir)
                    if not data:
                        self.logger.warning(
                            "failed to fetch chapter %s, skipping repair",
                            prev_cid,
                        )
                        continue
                    storage.upsert_chapter(data, self.DEFAULT_SOURCE_ID)
                    await async_jitter_sleep(
                        self.request_interval,
                        mul_spread=1.1,
                        max_sleep=self.request_interval + 2,
                    )

                next_cid = data.get("extra", {}).get("next_chapter_id")
                if not next_cid:
                    self.logger.warning(
                        "No next_chapter_id in data for %s",
                        prev_cid,
                    )
                    continue

                self.logger.info(
                    "repaired chapterId: set to %s (from prev %s)",
                    next_cid,
                    prev_cid,
                )
                chap["chapterId"] = next_cid
                prev_cid = next_cid

        self._save_book_info(book_id, book_info)
        return book_info

    async def _process_chapter(
        self,
        book_id: str,
        cid: str,
        html_dir: Path,
    ) -> ChapterDict | None:
        """
        Fetches, saves raw HTML, parses a single chapter,
        retrying up to self.retry_times.

        :return: ChapterDict on success, or None on failure.
        """
        for attempt in range(self.retry_times + 1):
            try:
                html_list = await self.fetcher.get_book_chapter(book_id, cid)
                self._save_html_pages(html_dir, cid, html_list)
                chap = await asyncio.to_thread(
                    self.parser.parse_chapter, html_list, cid
                )
                if not chap:
                    raise ValueError("Empty parse result")
                return chap
            except Exception as e:
                if attempt < self.retry_times:
                    self.logger.info(f"[ChapterWorker] Retry {cid} ({attempt+1}): {e}")
                    backoff = self.backoff_factor * (2**attempt)
                    await async_jitter_sleep(
                        base=backoff, mul_spread=1.2, max_sleep=backoff + 3
                    )
                else:
                    self.logger.warning(f"[ChapterWorker] Failed {cid}: {e}")
        return None
