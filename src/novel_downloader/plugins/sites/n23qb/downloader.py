#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n23qb.downloader
-----------------------------------------------

Downloader implementation for Qianbi novels, with chapter ID repair logic.
"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from novel_downloader.infra.persistence.chapter_storage import ChapterStorage
from novel_downloader.libs.time_utils import async_jitter_sleep
from novel_downloader.plugins.base.downloader import BaseDownloader
from novel_downloader.plugins.registry import registrar
from novel_downloader.plugins.utils.signals import STOP, Progress, StopToken
from novel_downloader.schemas import BookConfig, BookInfoDict, ChapterDict


@registrar.register_downloader()
class N23qbDownloader(BaseDownloader):
    """
    Downloader for n23qb (铅笔) novels.

    Repairs missing chapter IDs by following 'next' links, then downloads
    each chapter as a unit (fetch -> parse -> enqueue storage).
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
        The full download logic for a single book.

        :param book: BookConfig with at least 'book_id'.
        """
        book_id = book["book_id"]
        start_id = book.get("start_id")
        end_id = book.get("end_id")
        ignore_set = set(book.get("ignore_ids", []))

        raw_base = self._raw_data_dir / book_id
        raw_base.mkdir(parents=True, exist_ok=True)

        def cancelled() -> bool:
            return bool(cancel_event and cancel_event.is_set())

        with ChapterStorage(raw_base, priorities=self.PRIORITIES_MAP) as storage:
            # --- metadata ---
            book_info = await self._load_book_info(book_id=book_id)
            if not book_info:
                return

            book_info = await self._repair_chapter_ids(
                book_id,
                book_info,
                storage,
                cancel_event=cancel_event,
            )

            if cancelled():
                self.logger.info("Repair cancelled for book %s", book_id)
                return

            vols = book_info["volumes"]
            plan = self._select_chapter_ids(vols, start_id, end_id, ignore_set)
            if not plan:
                self.logger.info("Nothing to do after filtering: %s", book_id)
                return

            progress = Progress(total=len(plan), hook=progress_hook)

            # --- queues & batching ---
            cid_q: asyncio.Queue[str] = asyncio.Queue(maxsize=self._workers)
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

            # --- storage worker ---
            async def storage_worker() -> None:
                while True:
                    item = await save_q.get()
                    if isinstance(item, StopToken):
                        # drain anything still queued, then flush and exit
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
                        # cooperative cancel: exit once no more work
                        if cancelled() and cid_q.empty():
                            return
                        try:
                            cid = await asyncio.wait_for(cid_q.get(), timeout=0.5)
                        except TimeoutError:
                            # normal exit when producer finished and queue is empty
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
                    # allow graceful shutdown
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
            storage_task = asyncio.create_task(storage_worker())
            async with asyncio.TaskGroup() as tg:
                worker_tasks = [
                    tg.create_task(chapter_worker()) for _ in range(self._workers)
                ]
                producer_task = tg.create_task(producer())

            if cancel_event:

                async def cancel_watcher() -> None:
                    await cancel_event.wait()
                    if not producer_task.done():
                        producer_task.cancel()
                    for t in worker_tasks:
                        if not t.done():
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

    async def _repair_chapter_ids(
        self,
        book_id: str,
        book_info: BookInfoDict,
        storage: ChapterStorage,
        *,
        cancel_event: asyncio.Event | None = None,
    ) -> BookInfoDict:
        """
        Fill in missing chapterId fields by retrieving the previous chapter
        and following its 'next_cid'. Uses storage to avoid refetching.
        """

        def cancelled() -> bool:
            return bool(cancel_event and cancel_event.is_set())

        prev_cid: str = ""
        for vol in book_info["volumes"]:
            for chap in vol["chapters"]:
                if cancelled():
                    self.logger.info("Repair cancelled for book %s", book_id)
                    return book_info

                cid = chap.get("chapterId")
                if cid:
                    prev_cid = cid
                    continue

                if not prev_cid:
                    continue

                # missing id: try storage
                data = storage.get_best_chapter(prev_cid)
                if not data:
                    if cancelled():
                        return book_info

                    # fetch+parse previous to discover next
                    data = await self._process_chapter(book_id, prev_cid)
                    if not data:
                        self.logger.warning(
                            "Failed to fetch chapter %s, skipping repair",
                            prev_cid,
                        )
                        continue
                    storage.upsert_chapter(data, self.DEFAULT_SOURCE_ID)
                    if cancelled():
                        return book_info
                    await async_jitter_sleep(
                        self._request_interval,
                        mul_spread=1.1,
                        max_sleep=self._request_interval + 2,
                    )

                next_cid = data.get("extra", {}).get("next_cid")
                if not next_cid:
                    self.logger.warning("No next_cid in data for %s", prev_cid)
                    continue

                self.logger.info(
                    "Repaired chapterId: set to %s (from prev %s)",
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
                return chap
            except Exception as e:
                if attempt < self._retry_times:
                    self.logger.info(f"Retry chapter {cid} ({attempt+1}): {e}")
                    backoff = self._backoff_factor * (2**attempt)
                    await async_jitter_sleep(
                        base=backoff, mul_spread=1.2, max_sleep=backoff + 3
                    )
                else:
                    self.logger.warning(f"Failed chapter {cid}: {e}")
        return None
