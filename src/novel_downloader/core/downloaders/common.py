#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.common
----------------------------------------

Concrete downloader implementation with a generic async pipeline for common novel sites
"""

import asyncio
from collections.abc import Awaitable, Callable
from contextlib import suppress
from typing import Any

from novel_downloader.core.downloaders.base import BaseDownloader
from novel_downloader.core.downloaders.signals import STOP, Progress, StopToken
from novel_downloader.models import BookConfig, ChapterDict
from novel_downloader.utils.chapter_storage import ChapterStorage
from novel_downloader.utils.time_utils import async_jitter_sleep


class CommonDownloader(BaseDownloader):
    """
    Specialized Async downloader for "common" novel sites.
    """

    async def _download_one(
        self,
        book: BookConfig,
        *,
        progress_hook: Callable[[int, int], Awaitable[None]] | None = None,
        cancel_event: asyncio.Event | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Sentinel-based pipeline with cancellation:

        Producer -> ChapterWorkers -> StorageWorker.

        On cancel: stop producing, workers finish at most one chapter,
        storage drains, flushes, and exits.
        """
        book_id = self._normalize_book_id(book["book_id"])
        start_id = book.get("start_id")
        end_id = book.get("end_id")
        ignore_set = set(book.get("ignore_ids", []))

        raw_base = self._raw_data_dir / book_id
        raw_base.mkdir(parents=True, exist_ok=True)

        def cancelled() -> bool:
            return bool(cancel_event and cancel_event.is_set())

        # --- metadata ---
        book_info = await self._load_book_info(book_id=book_id)
        if not book_info:
            return

        vols = book_info["volumes"]
        plan = self._select_chapter_ids(vols, start_id, end_id, ignore_set)
        if not plan:
            self.logger.info("Nothing to do after filtering: %s", book_id)
            return

        progress = Progress(total=len(plan), hook=progress_hook)

        # --- queues & batching ---
        cid_q: asyncio.Queue[str | StopToken] = asyncio.Queue(maxsize=self._workers * 2)
        save_q: asyncio.Queue[ChapterDict | StopToken] = asyncio.Queue(
            maxsize=self._workers * 5
        )
        batch: list[ChapterDict] = []

        async def flush_batch() -> None:
            if not batch:
                return
            try:
                storage.upsert_chapters(batch, self.DEFAULT_SOURCE_ID)
            except Exception as e:
                self.logger.error(
                    "Storage batch upsert failed (size=%d): %s",
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

            async def drain_nonblocking() -> None:
                # Pull everything currently buffered without blocking
                nonlocal stop_count
                while True:
                    try:
                        nxt = save_q.get_nowait()
                    except asyncio.QueueEmpty:
                        break
                    if isinstance(nxt, StopToken):
                        stop_count += 1
                    else:
                        batch.append(nxt)
                        if len(batch) >= self._storage_batch_size:
                            await flush_batch()

            while True:
                try:
                    item = await save_q.get()
                except asyncio.CancelledError:
                    # Shouldn't happen, but be defensive:
                    await flush_batch()
                    return

                if isinstance(item, StopToken):
                    stop_count += 1
                    if stop_count == self._workers:
                        await flush_batch()
                        return
                    continue

                # Normal chapter
                batch.append(item)
                if len(batch) >= self._storage_batch_size:
                    await flush_batch()

                if cancelled():
                    await drain_nonblocking()
                    await flush_batch()
                    return

        # --- stage: chapter worker ---
        async def chapter_worker() -> None:
            """
            Fetch + parse with retry, then enqueue to save_q.

            Exits on STOP, or early if cancel is set before starting a new fetch.
            """
            try:
                while True:
                    cid = await cid_q.get()
                    if isinstance(cid, StopToken):
                        # Propagate one STOP to storage and exit.
                        with suppress(asyncio.QueueFull):
                            save_q.put_nowait(STOP)
                        return

                    if cancelled():
                        with suppress(asyncio.QueueFull):
                            save_q.put_nowait(STOP)
                        return

                    chap = await self._process_chapter(book_id, cid)
                    if chap:
                        await save_q.put(chap)

                    # polite pacing
                    await async_jitter_sleep(
                        self._request_interval,
                        mul_spread=1.1,
                        max_sleep=self._request_interval + 2,
                    )
            except asyncio.CancelledError:
                with suppress(asyncio.QueueFull):
                    save_q.put_nowait(STOP)
                return

        # --- stage: producer ---
        async def producer() -> None:
            """
            Enqueue chapter IDs (respecting start/end/skip_existing).

            Always sends STOP x workers at the end (even if cancelled early),
            so chapter workers can exit deterministically.
            """
            try:
                for cid in plan:
                    if cancelled():
                        break
                    if self._skip_existing and storage.exists(cid):
                        # Count as completed but don't enqueue.
                        await progress.bump(1)
                    else:
                        await cid_q.put(cid)
            finally:
                for _ in range(self._workers):
                    with suppress(asyncio.CancelledError):
                        await cid_q.put(STOP)

        # --- run the pipeline ---
        with ChapterStorage(raw_base, priorities=self.PRIORITIES_MAP) as storage:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(storage_worker())
                worker_tasks = [
                    tg.create_task(chapter_worker()) for _ in range(self._workers)
                ]
                producer_task = tg.create_task(producer())

                if cancel_event:

                    async def cancel_watcher() -> None:
                        await cancel_event.wait()
                        producer_task.cancel()
                        for t in worker_tasks:
                            t.cancel()

                        with suppress(Exception):
                            while True:
                                cid_q.get_nowait()

                    tg.create_task(cancel_watcher())

        # --- done ---
        if cancelled():
            self.logger.info(
                "Novel '%s' cancelled: flushed %d/%d chapters.",
                book_info.get("book_name", "unknown"),
                progress.done,
                progress.total,
            )
        else:
            self.logger.info(
                "Novel '%s' download completed.",
                book_info.get("book_name", "unknown"),
            )

    async def _process_chapter(
        self,
        book_id: str,
        cid: str,
    ) -> ChapterDict | None:
        """
        Fetches, saves raw HTML, parses a single chapter,
        retrying up to self.retry_times.

        :return: ChapterDict on success, or None on failure.
        """
        for attempt in range(self._retry_times + 1):
            try:
                html_list = await self.fetcher.get_book_chapter(book_id, cid)
                self._save_html_pages(book_id, cid, html_list)
                chap = await asyncio.to_thread(
                    self.parser.parse_chapter, html_list, cid
                )
                if not chap:
                    raise ValueError("Empty parse result")
                imgs = self._extract_img_urls(chap["content"])
                img_dir = self._raw_data_dir / book_id / "images"
                await self.fetcher.download_images(img_dir, imgs)
                return chap
            except Exception as e:
                if attempt < self._retry_times:
                    self.logger.info("Retry chapter %s (%s): %s", cid, attempt + 1, e)
                    backoff = self._backoff_factor * (2**attempt)
                    await async_jitter_sleep(
                        base=backoff, mul_spread=1.2, max_sleep=backoff + 3
                    )
                else:
                    self.logger.warning("Failed chapter %s: %s", cid, e)
        return None

    @staticmethod
    def _normalize_book_id(book_id: str) -> str:
        """
        Normalize a book identifier.

        Subclasses may override this method to transform the book ID
        into their preferred format.
        """
        return book_id.replace("/", "-")
