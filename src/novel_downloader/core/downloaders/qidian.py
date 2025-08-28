#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.qidian
----------------------------------------

Downloader implementation for Qidian novels,
with handling for restricted and encrypted chapters
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
    ChapterDict,
    DownloaderConfig,
)
from novel_downloader.utils import (
    ChapterStorage,
    async_jitter_sleep,
)


@register_downloader(site_keys=["qidian", "qd"])
class QidianDownloader(BaseDownloader):
    """
    Specialized downloader for Qidian (起点) novels.

    Processes each chapter in a single worker that
    handles fetch -> parse -> enqueue storage.
    """

    DEFAULT_SOURCE_ID = 0
    ENCRYPTED_SOURCE_ID = 1
    PRIORITIES_MAP = {
        DEFAULT_SOURCE_ID: 0,
        ENCRYPTED_SOURCE_ID: 1,
    }

    def __init__(
        self,
        fetcher: FetcherProtocol,
        parser: ParserProtocol,
        config: DownloaderConfig,
    ):
        config.request_interval = max(1.0, config.request_interval)
        super().__init__(fetcher, parser, config, "qidian")

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
        NUM_WORKERS = 1

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
            # ---- metadata ---
            book_info = await self.load_book_info(book_id=book_id, html_dir=html_dir)
            if not book_info:
                return

            vols = book_info["volumes"]
            total_chapters = sum(len(v["chapters"]) for v in vols)
            if total_chapters == 0:
                self.logger.warning("%s 书籍没有章节可下载: %s", TAG, book_id)
                return

            progress = Progress(total_chapters, progress_hook)

            # ---- queues & batching ---
            cid_q: asyncio.Queue[str | StopToken] = asyncio.Queue()
            save_q: asyncio.Queue[ChapterDict | StopToken] = asyncio.Queue()
            default_batch: list[ChapterDict] = []
            encrypted_batch: list[ChapterDict] = []

            def select_batch(chap: ChapterDict) -> tuple[list[ChapterDict], int]:
                # set extra.encrypted (by parser); default to plain if absent.
                if chap.get("extra", {}).get("encrypted", False):
                    return encrypted_batch, self.ENCRYPTED_SOURCE_ID
                return default_batch, self.DEFAULT_SOURCE_ID

            async def flush_batch(batch: list[ChapterDict], src: int) -> None:
                if not batch:
                    return
                try:
                    chapter_storage.upsert_chapters(batch, src)
                except Exception as e:
                    self.logger.error(
                        "[Storage] batch upsert failed (size=%d, src=%d): %s",
                        len(batch),
                        src,
                        e,
                        exc_info=True,
                    )
                else:
                    await progress.bump(len(batch))
                finally:
                    batch.clear()

            async def flush_all() -> None:
                await flush_batch(default_batch, self.DEFAULT_SOURCE_ID)
                await flush_batch(encrypted_batch, self.ENCRYPTED_SOURCE_ID)

            # ---- workers ---
            sem = asyncio.Semaphore(self.workers)

            async def storage_worker() -> None:
                """
                Consumes parsed chapters, batches by source, flushes on threshold.

                Terminates after receiving STOP from each chapter worker.

                On cancel: drains queue, flushes once, then waits for remaining STOPs.
                """
                stop_count = 0
                while True:
                    chap = await save_q.get()
                    if isinstance(chap, StopToken):
                        stop_count += 1
                        if stop_count == NUM_WORKERS:
                            await flush_all()
                            return
                        continue

                    batch, src = select_batch(chap)
                    batch.append(chap)
                    if len(batch) >= self.storage_batch_size:
                        await flush_batch(batch, src)

                    if cancelled():
                        # Drain whatever is already parsed
                        try:
                            while True:
                                nxt = save_q.get_nowait()
                                if isinstance(nxt, StopToken):
                                    stop_count += 1
                                else:
                                    nbatch, nsrc = select_batch(nxt)
                                    nbatch.append(nxt)
                        except asyncio.QueueEmpty:
                            pass
                        await flush_all()
                        # Wait for remaining STOPs to arrive
                        while stop_count < NUM_WORKERS:
                            nxt = await save_q.get()
                            if nxt is STOP:
                                stop_count += 1
                        return

            async def chapter_worker() -> None:
                """
                Single worker: fetch + parse with retry, then enqueue ChapterDict.

                Exits on STOP. If cancelled, does not start a new fetch; signals STOP.
                """
                while True:
                    cid = await cid_q.get()
                    if isinstance(cid, StopToken):
                        await save_q.put(STOP)
                        return

                    if not cid or cid in ignore_set:
                        continue

                    if cancelled():
                        await save_q.put(STOP)
                        return

                    async with sem:
                        chap = await self._process_chapter(book_id, cid, html_dir)
                    if chap and not cancelled():
                        await save_q.put(chap)

                    await async_jitter_sleep(
                        self.request_interval,
                        mul_spread=1.1,
                        max_sleep=self.request_interval + 2,
                    )

            async def producer() -> None:
                """
                Enqueue chapter IDs respecting start/end/skip_existing.

                Always emits STOP x NUM_WORKERS at the end (even if cancelled early).
                """
                try:
                    async for cid in self._chapter_ids(vols, start_id, end_id):
                        if cancelled():
                            break
                        if self.skip_existing and (
                            chapter_storage.exists(cid, self.DEFAULT_SOURCE_ID)
                            or chapter_storage.exists(cid, self.ENCRYPTED_SOURCE_ID)
                        ):
                            # Already have either variant; count as done.
                            await progress.bump(1)
                        else:
                            await cid_q.put(cid)
                finally:
                    for _ in range(NUM_WORKERS):
                        await cid_q.put(STOP)

            # ---- run tasks ---
            async with asyncio.TaskGroup() as tg:
                tg.create_task(storage_worker())
                for _ in range(NUM_WORKERS):
                    tg.create_task(chapter_worker())
                tg.create_task(producer())

            # ---- done ---
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

    @staticmethod
    def _check_restricted(html_list: list[str]) -> bool:
        """
        Return True if page content indicates access restriction
        (e.g. not subscribed/purchased).

        :param html_list: Raw HTML string.
        """
        if not html_list:
            return True
        markers = ["这是VIP章节", "需要订阅", "订阅后才能阅读"]
        return any(m in html_list[0] for m in markers)

    @staticmethod
    def _check_encrypted(html_list: list[str]) -> bool:
        if not html_list:
            return True
        return '"cES":2' in html_list[0]

    async def _process_chapter(
        self,
        book_id: str,
        cid: str,
        html_dir: Path,
    ) -> ChapterDict | None:
        """
        Fetch, debug-save, parse a single chapter with retries.

        :return: ChapterDict on success, or None on failure.
        """
        for attempt in range(self.retry_times + 1):
            try:
                html_list = await self.fetcher.get_book_chapter(book_id, cid)
                if self._check_restricted(html_list):
                    self.logger.info(
                        "[ChapterWorker] Restricted content detected: %s", cid
                    )
                    return None
                encrypted = self._check_encrypted(html_list)

                folder = "html_encrypted" if encrypted else "html_plain"
                self._save_html_pages(html_dir / folder, cid, html_list)

                chap = await asyncio.to_thread(
                    self.parser.parse_chapter, html_list, cid
                )
                if encrypted and not chap:
                    self.logger.info(
                        "[ChapterWorker] Fail for encrypted chapter: %s", cid
                    )
                    return None
                if not chap:
                    raise ValueError("Empty parse result")
                return chap

            except Exception as e:
                if attempt < self.retry_times:
                    self.logger.info(
                        "[ChapterWorker] Retry %s (%s): %s", cid, attempt + 1, e
                    )
                    backoff = self.backoff_factor * (2**attempt)
                    await async_jitter_sleep(
                        base=backoff,
                        mul_spread=1.2,
                        max_sleep=backoff + 3,
                    )
                else:
                    self.logger.warning("[ChapterWorker] Failed %s: %s", cid, e)
        return None
