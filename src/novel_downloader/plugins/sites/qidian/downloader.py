#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.qidian.downloader
------------------------------------------------

Downloader implementation for Qidian novels,
with handling for restricted and encrypted chapters
"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any, ClassVar

from novel_downloader.infra.persistence.chapter_storage import ChapterStorage
from novel_downloader.libs.time_utils import async_jitter_sleep
from novel_downloader.plugins.base.downloader import BaseDownloader
from novel_downloader.plugins.protocols import FetcherProtocol, ParserProtocol
from novel_downloader.plugins.registry import registrar
from novel_downloader.plugins.utils.signals import STOP, Progress, StopToken
from novel_downloader.schemas import BookConfig, ChapterDict, DownloaderConfig


@registrar.register_downloader()
class QidianDownloader(BaseDownloader):
    """
    Specialized downloader for Qidian (起点) novels.

    Processes each chapter in a single worker that
    handles fetch -> parse -> enqueue storage.
    """

    DEFAULT_SOURCE_ID: ClassVar[int] = 0
    ENCRYPTED_SOURCE_ID: ClassVar[int] = 1
    PRIORITIES_MAP: ClassVar[dict[int, int]] = {
        DEFAULT_SOURCE_ID: 0,
        ENCRYPTED_SOURCE_ID: 1,
    }

    def __init__(
        self,
        fetcher: FetcherProtocol,
        parser: ParserProtocol,
        config: DownloaderConfig,
        site: str,
    ):
        super().__init__(fetcher, parser, config, site)
        self._request_interval = max(1.0, config.request_interval)

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
        NUM_WORKERS = 1

        book_id = book["book_id"]
        start_id = book.get("start_id")
        end_id = book.get("end_id")
        ignore_set = set(book.get("ignore_ids", []))

        raw_base = self._raw_data_dir / book_id
        raw_base.mkdir(parents=True, exist_ok=True)

        def cancelled() -> bool:
            return bool(cancel_event and cancel_event.is_set())

        # ---- metadata ---
        book_info = await self._load_book_info(book_id=book_id)
        if not book_info:
            return

        vols = book_info["volumes"]
        plan = self._select_chapter_ids(vols, start_id, end_id, ignore_set)
        if not plan:
            self.logger.info("Nothing to do after filtering: %s", book_id)
            return

        progress = Progress(total=len(plan), hook=progress_hook)

        # ---- queues & batching ---
        cid_q: asyncio.Queue[str] = asyncio.Queue(maxsize=2)
        save_q: asyncio.Queue[ChapterDict | StopToken] = asyncio.Queue(maxsize=10)
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
                storage.upsert_chapters(batch, src)
            except Exception as e:
                self.logger.error(
                    "Storage batch upsert failed (size=%d, src=%d): %s",
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
        async def storage_worker() -> None:
            while True:
                item = await save_q.get()
                if isinstance(item, StopToken):
                    # drain any remaining chapters, then flush both batches
                    while not save_q.empty():
                        nxt = save_q.get_nowait()
                        if not isinstance(nxt, StopToken):
                            nbatch, nsrc = select_batch(nxt)
                            nbatch.append(nxt)
                            if len(nbatch) >= self._storage_batch_size:
                                await flush_batch(nbatch, nsrc)
                    await flush_all()
                    return

                batch, src = select_batch(item)
                batch.append(item)
                if len(batch) >= self._storage_batch_size:
                    await flush_batch(batch, src)

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
                if self._skip_existing and storage.exists(cid, self.DEFAULT_SOURCE_ID):
                    # Already have plain chapter; treat as done.
                    await progress.bump(1)
                else:
                    await cid_q.put(cid)

        # ---- run tasks ---
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
    ) -> ChapterDict | None:
        """
        Fetch, debug-save, parse a single chapter with retries.

        :return: ChapterDict on success, or None on failure.
        """
        for attempt in range(self._retry_times + 1):
            try:
                html_list = await self.fetcher.get_book_chapter(book_id, cid)
                if self._check_restricted(html_list):
                    self.logger.info("Restricted chapter content detected: %s", cid)
                    return None
                encrypted = self._check_encrypted(html_list)

                folder = "html_encrypted" if encrypted else "html_plain"
                self._save_html_pages(book_id, cid, html_list, folder=folder)

                chap = await asyncio.to_thread(
                    self.parser.parse_chapter, html_list, cid
                )
                if encrypted and not chap:
                    self.logger.info("Fail for encrypted chapter: %s", cid)
                    return None
                if not chap:
                    raise ValueError("Empty parse result")
                return chap

            except Exception as e:
                if attempt < self._retry_times:
                    self.logger.info("Retry chapter %s (%s): %s", cid, attempt + 1, e)
                    backoff = self._backoff_factor * (2**attempt)
                    await async_jitter_sleep(
                        base=backoff,
                        mul_spread=1.2,
                        max_sleep=backoff + 3,
                    )
                else:
                    self.logger.warning("Failed chapter %s: %s", cid, e)
        return None
