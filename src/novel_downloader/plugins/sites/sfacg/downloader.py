#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.sfacg.downloader
-----------------------------------------------

"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from novel_downloader.infra.persistence.chapter_storage import ChapterStorage
from novel_downloader.libs.time_utils import async_jitter_sleep
from novel_downloader.plugins.base.downloader import BaseDownloader
from novel_downloader.plugins.registry import registrar
from novel_downloader.plugins.utils.signals import STOP, Progress, StopToken
from novel_downloader.schemas import BookConfig, ChapterDict


@registrar.register_downloader()
class SfacgDownloader(BaseDownloader):
    """
    Specialized Async downloader for sfacg novel sites.
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
        NUM_WORKERS = 1

        book_id = book["book_id"]
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
        cid_q: asyncio.Queue[str] = asyncio.Queue(maxsize=2)
        save_q: asyncio.Queue[ChapterDict | StopToken] = asyncio.Queue(maxsize=10)
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

        # --- storage worker ---
        async def storage_worker() -> None:
            while True:
                item = await save_q.get()
                if isinstance(item, StopToken):
                    # drain any remaining items before exiting
                    while not save_q.empty():
                        nxt = save_q.get_nowait()
                        if not isinstance(nxt, StopToken):
                            batch.append(nxt)
                            if len(batch) >= self._storage_batch_size:
                                await flush_batch()
                    await flush_batch()
                    return
                batch.append(item)
                if len(batch) >= self._storage_batch_size:
                    await flush_batch()

        # --- chapter worker ---
        async def chapter_worker() -> None:
            try:
                while True:
                    if cancelled() and cid_q.empty():
                        return
                    try:
                        cid = await asyncio.wait_for(cid_q.get(), timeout=0.5)
                    except TimeoutError:
                        if producer_task.done() and cid_q.empty():
                            return
                        continue

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
                # allow graceful unwinding
                return

        # --- producer ---
        async def producer() -> None:
            for cid in plan:
                if cancelled():
                    break
                if self._skip_existing and storage.exists(cid):
                    await progress.bump(1)
                else:
                    await cid_q.put(cid)

        # --- run the pipeline ---
        with ChapterStorage(raw_base, priorities=self.PRIORITIES_MAP) as storage:
            storage_task = asyncio.create_task(storage_worker())
            async with asyncio.TaskGroup() as tg:
                worker_tasks = [
                    tg.create_task(chapter_worker()) for _ in range(NUM_WORKERS)
                ]
                producer_task = tg.create_task(producer())

            if cancel_event:

                async def cancel_watcher() -> None:
                    await cancel_event.wait()
                    producer_task.cancel()
                    for t in worker_tasks:
                        t.cancel()

                asyncio.create_task(cancel_watcher())

            await save_q.put(STOP)
            await storage_task

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
                if html_list and "本章为VIP章节" in html_list[0]:
                    self.logger.warning(
                        "VIP chapter %s :: not purchased, skipping",
                        cid,
                    )
                    return None

                chap = await asyncio.to_thread(
                    self.parser.parse_chapter, html_list, cid
                )
                if not chap:
                    # check VIP indicator
                    if html_list and "/ajax/ashx/common.ashx" in html_list[0]:
                        self.logger.warning(
                            "VIP chapter %s :: no content after parse (skipping)",
                            cid,
                        )
                        return None
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
