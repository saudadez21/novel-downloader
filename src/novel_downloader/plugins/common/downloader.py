#!/usr/bin/env python3
"""
novel_downloader.plugins.common.downloader
------------------------------------------

Concrete downloader implementation with a generic async pipeline for common novel sites
"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any

from novel_downloader.infra.persistence.chapter_storage import ChapterStorage
from novel_downloader.libs.time_utils import async_jitter_sleep
from novel_downloader.plugins.base.downloader import BaseDownloader
from novel_downloader.plugins.utils.signals import STOP, Progress, StopToken
from novel_downloader.schemas import (
    BookConfig,
    BookInfoDict,
    ChapterDict,
    VolumeInfoDict,
)


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
        book_id = self._normalize_book_id(book.book_id)
        start_id = book.start_id
        end_id = book.end_id
        ignore_set = set(book.ignore_ids or [])

        raw_base = self._raw_data_dir / book_id
        raw_base.mkdir(parents=True, exist_ok=True)

        def cancelled() -> bool:
            return bool(cancel_event and cancel_event.is_set())

        # --- metadata ---
        book_info = await self._load_book_info(book_id=book_id)
        with ChapterStorage(raw_base, filename="chapter.raw.sqlite") as storage:
            book_info = await self._repair_chapter_ids(
                book_id,
                book_info,
                storage,
                cancel_event=cancel_event,
            )

        vols = book_info["volumes"]
        plan = self._select_chapter_ids(vols, start_id, end_id, ignore_set)
        if not plan:
            self.logger.info(
                "Nothing to do after filtering (site=%s, book=%s)", self._site, book_id
            )
            return

        progress = Progress(total=len(plan), hook=progress_hook)

        # --- queues & batching ---
        cid_q: asyncio.Queue[str] = asyncio.Queue(maxsize=self.workers * 5)
        save_q: asyncio.Queue[ChapterDict | StopToken] = asyncio.Queue(
            maxsize=self.workers * 5
        )
        batch: list[ChapterDict] = []

        async def flush_batch() -> None:
            if not batch:
                return
            try:
                storage.upsert_chapters(batch)
            except Exception as e:
                self.logger.error(
                    "Storage batch upsert failed (site=%s, book=%s, size=%d): %s",
                    self._site,
                    book_id,
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
        with ChapterStorage(raw_base, filename="chapter.raw.sqlite") as storage:
            storage_task = asyncio.create_task(storage_worker())
            async with asyncio.TaskGroup() as tg:
                worker_tasks = [
                    tg.create_task(chapter_worker()) for _ in range(self.workers)
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
                "Download cancelled for site=%s book=%s (%d/%d chapters flushed)",
                self._site,
                book_id,
                progress.done,
                progress.total,
            )
        else:
            self.logger.info(
                "Download completed for site=%s book=%s",
                self._site,
                book_id,
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

                if self._is_access_limited(html_list):
                    self.logger.warning(
                        "Access limited (site=%s, book=%s, chapter=%s)",
                        self._site,
                        book_id,
                        cid,
                    )
                    return None

                chap = await asyncio.to_thread(
                    self.parser.parse_chapter, html_list, cid
                )
                if not chap:
                    if self._skip_empty_chapter(html_list):
                        self.logger.warning(
                            "Empty parse result (site=%s, book=%s, chapter=%s)",
                            self._site,
                            book_id,
                            cid,
                        )
                        return None
                    raise ValueError("Empty parse result")

                imgs = self._extract_img_urls(chap["extra"])
                img_dir = self._raw_data_dir / book_id / "images"
                await self.fetcher.download_images(img_dir, imgs)
                return chap
            except Exception as e:
                if attempt < self._retry_times:
                    self.logger.info(
                        "Retrying (site=%s, book=%s, chapter=%s, attempt=%d): %s",
                        self._site,
                        book_id,
                        cid,
                        attempt + 1,
                        e,
                    )
                    backoff = self._backoff_factor * (2**attempt)
                    await async_jitter_sleep(
                        base=backoff, mul_spread=1.2, max_sleep=backoff + 3
                    )
                else:
                    self.logger.warning(
                        "Failed chapter (site=%s, book=%s, chapter=%s): %s",
                        self._site,
                        book_id,
                        cid,
                        e,
                    )
        return None

    def _extract_img_urls(self, extra: dict[str, Any]) -> list[str]:
        """
        Extract all image URLs from 'extra' field.
        """
        if not isinstance(extra, dict):
            return []

        image_positions = extra.get("image_positions")
        if not isinstance(image_positions, dict):
            return []

        urls: list[str] = []
        for line_no, urls_in_line in image_positions.items():
            if not isinstance(urls_in_line, list | tuple):
                self.logger.debug(
                    "image_positions[%r] expected list/tuple, got %r",
                    line_no,
                    type(urls_in_line),
                )
                continue
            for url in urls_in_line:
                if isinstance(url, str) and url.startswith("http"):
                    urls.append(url)
                else:
                    self.logger.debug(
                        "Invalid image URL type or format at line %r: %r",
                        line_no,
                        url,
                    )

        return urls

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
                    self.logger.info(
                        "Repair cancelled (site=%s, book=%s)", self._site, book_id
                    )
                    return book_info

                cid = chap.get("chapterId")
                if cid:
                    prev_cid = cid
                    continue

                if not prev_cid:
                    continue

                # missing id: try storage
                data = storage.get_chapter(prev_cid)
                if not data:
                    if cancelled():
                        return book_info

                    # fetch+parse previous to discover next
                    data = await self._process_chapter(book_id, prev_cid)
                    if not data:
                        self.logger.warning(
                            "Failed to fetch chapter (site=%s, book=%s, prev=%s) during repair",  # noqa: E501
                            self._site,
                            book_id,
                            prev_cid,
                        )
                        continue
                    storage.upsert_chapter(data)
                    if cancelled():
                        return book_info
                    await async_jitter_sleep(
                        self._request_interval,
                        mul_spread=1.1,
                        max_sleep=self._request_interval + 2,
                    )

                next_cid = data.get("extra", {}).get("next_cid")
                if not next_cid:
                    self.logger.warning(
                        "No next_cid (site=%s, book=%s, prev=%s)",
                        self._site,
                        book_id,
                        prev_cid,
                    )
                    continue

                self.logger.info(
                    "Repaired chapterId (site=%s, book=%s): %s <- %s",
                    self._site,
                    book_id,
                    next_cid,
                    prev_cid,
                )
                chap["chapterId"] = next_cid
                prev_cid = next_cid

        self._save_book_info(book_id, book_info)
        return book_info

    @staticmethod
    def _select_chapter_ids(
        vols: list[VolumeInfoDict],
        start_id: str | None,
        end_id: str | None,
        ignore: set[str],
    ) -> list[str]:
        seen_start = start_id is None
        out: list[str] = []
        for vol in vols:
            for chap in vol["chapters"]:
                cid = chap.get("chapterId")
                if not cid:
                    continue
                if not seen_start:
                    if cid == start_id:
                        seen_start = True
                    else:
                        continue
                if cid not in ignore and chap.get("accessible", True):
                    out.append(cid)
                if end_id is not None and cid == end_id:
                    return out
        return out

    @staticmethod
    def _normalize_book_id(book_id: str) -> str:
        """
        Normalize a book identifier.

        Subclasses may override this method to transform the book ID
        into their preferred format.
        """
        return book_id.replace("/", "-")

    def _is_access_limited(self, html_list: list[str]) -> bool:
        """
        Return True if page content indicates access restriction
        (e.g. login required, paywall, VIP, subscription, etc.)

        :param html_list: List of raw HTML strings.
        """
        return False

    def _skip_empty_chapter(self, html_list: list[str]) -> bool:
        """
        Return True if parse_chapter returns empty but should be skipped.
        """
        return False


class DualBatchDownloader(CommonDownloader):
    """
    Specialized Async downloader for sites that require
    two storage batches (e.g., marking chapters with need_refetch=True).
    """

    def _need_refetch(self, chap: ChapterDict) -> bool:
        """Override this hook to decide if a chapter needs refetch."""
        return False

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
        book_id = self._normalize_book_id(book.book_id)
        start_id = book.start_id
        end_id = book.end_id
        ignore_set = set(book.ignore_ids or [])

        raw_base = self._raw_data_dir / book_id
        raw_base.mkdir(parents=True, exist_ok=True)

        def cancelled() -> bool:
            return bool(cancel_event and cancel_event.is_set())

        # ---- metadata ---
        book_info = await self._load_book_info(book_id=book_id)
        with ChapterStorage(raw_base, filename="chapter.raw.sqlite") as storage:
            book_info = await self._repair_chapter_ids(
                book_id,
                book_info,
                storage,
                cancel_event=cancel_event,
            )

        vols = book_info["volumes"]
        plan = self._select_chapter_ids(vols, start_id, end_id, ignore_set)
        if not plan:
            self.logger.info(
                "Nothing to do after filtering (site=%s, book=%s)", self._site, book_id
            )
            return

        progress = Progress(total=len(plan), hook=progress_hook)

        # ---- queues & batching ---
        cid_q: asyncio.Queue[str] = asyncio.Queue(maxsize=2)
        save_q: asyncio.Queue[ChapterDict | StopToken] = asyncio.Queue(maxsize=10)
        batch_plain: list[ChapterDict] = []
        batch_refetch: list[ChapterDict] = []

        async def flush_batch(batch: list[ChapterDict], need_refetch: bool) -> None:
            if not batch:
                return
            try:
                # need_refetch=True for encrypted, False for plain
                storage.upsert_chapters(batch, need_refetch=need_refetch)
            except Exception as e:
                self.logger.error(
                    "Storage batch upsert failed (site=%s, book=%s, size=%d, need_refetch=%s): %s",  # noqa: E501
                    self._site,
                    book_id,
                    len(batch),
                    need_refetch,
                    e,
                    exc_info=True,
                )
            else:
                await progress.bump(len(batch))
            finally:
                batch.clear()

        async def flush_all() -> None:
            await flush_batch(batch_plain, need_refetch=False)
            await flush_batch(batch_refetch, need_refetch=True)

        # ---- workers ---
        async def storage_worker() -> None:
            while True:
                item = await save_q.get()
                if isinstance(item, StopToken):
                    # drain any remaining chapters, then flush both batches
                    while not save_q.empty():
                        nxt = save_q.get_nowait()
                        if isinstance(nxt, StopToken):
                            continue
                        target_need = self._need_refetch(nxt)
                        target_batch = batch_refetch if target_need else batch_plain
                        target_batch.append(nxt)
                        if len(target_batch) >= self._storage_batch_size:
                            await flush_batch(target_batch, need_refetch=target_need)
                    await flush_all()
                    return

                target_need = self._need_refetch(item)
                target_batch = batch_refetch if target_need else batch_plain
                target_batch.append(item)
                if len(target_batch) >= self._storage_batch_size:
                    await flush_batch(target_batch, need_refetch=target_need)

        async def chapter_worker() -> None:
            try:
                while True:
                    if cancelled() and cid_q.empty():
                        return
                    try:
                        cid = await asyncio.wait_for(cid_q.get(), timeout=0.5)
                    except TimeoutError:
                        # normal shutdown condition
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

        async def producer() -> None:
            for cid in plan:
                if cancelled():
                    break
                # Skip only if *know* it exists and does NOT need refetch.
                # Unknown ids default to need_refetch=True -> not skipped.
                if self._skip_existing and not storage.need_refetch(cid):
                    await progress.bump(1)
                else:
                    await cid_q.put(cid)

        # ---- run tasks ---
        with ChapterStorage(raw_base, filename="chapter.raw.sqlite") as storage:
            storage_task = asyncio.create_task(storage_worker())
            async with asyncio.TaskGroup() as tg:
                worker_tasks = [
                    tg.create_task(chapter_worker()) for _ in range(self.workers)
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

        # ---- done ---
        if cancelled():
            self.logger.info(
                "Download cancelled for site=%s book=%s (%d/%d chapters flushed)",
                self._site,
                book_id,
                progress.done,
                progress.total,
            )
        else:
            self.logger.info(
                "Download completed for site=%s book=%s",
                self._site,
                book_id,
            )
