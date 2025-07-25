#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.qidian
----------------------------------------

"""

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from novel_downloader.core.downloaders.base import BaseDownloader
from novel_downloader.core.downloaders.registry import register_downloader
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
    async_sleep_with_random_delay,
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
        super().__init__(fetcher, parser, config, "qidian", self.PRIORITIES_MAP)

    async def _download_one(
        self,
        book: BookConfig,
        *,
        progress_hook: Callable[[int, int], Awaitable[None]] | None = None,
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
            priorities=self._priorities,
        )
        chapter_storage.connect()

        # load or fetch metadata
        book_info = await self.load_book_info(book_id=book_id, html_dir=html_dir)
        if not book_info:
            return

        vols = book_info["volumes"]
        total_chapters = sum(len(v["chapters"]) for v in vols)
        if total_chapters == 0:
            self.logger.warning("%s 书籍没有章节可下载: %s", TAG, book_id)
            return

        # concurrency primitives
        sem = asyncio.Semaphore(self.workers)
        cid_q: asyncio.Queue[str | None] = asyncio.Queue()
        save_q: asyncio.Queue[ChapterDict | None] = asyncio.Queue()
        default_batch: list[ChapterDict] = []
        encrypted_batch: list[ChapterDict] = []
        completed = 0

        def _select(batch_item: ChapterDict) -> tuple[list[ChapterDict], int]:
            if batch_item.get("extra", {}).get("encrypted", False):
                return encrypted_batch, self.ENCRYPTED_SOURCE_ID
            return default_batch, self.DEFAULT_SOURCE_ID

        async def _flush(batch: list[ChapterDict], src: int) -> None:
            nonlocal completed
            if not batch:
                return
            try:
                chapter_storage.upsert_chapters(batch, src)
            except Exception as e:
                self.logger.error(
                    "[Storage] batch upsert failed (size=%d, source=%d): %s",
                    len(batch),
                    src,
                    e,
                    exc_info=True,
                )
            else:
                completed += len(batch)
                if progress_hook:
                    await progress_hook(completed, total_chapters)
            finally:
                batch.clear()

        async def storage_worker(q: asyncio.Queue[ChapterDict | None]) -> None:
            while True:
                chap = await q.get()
                q.task_done()
                if chap is None:
                    # final flush before exit
                    await _flush(default_batch, self.DEFAULT_SOURCE_ID)
                    await _flush(encrypted_batch, self.ENCRYPTED_SOURCE_ID)
                    break
                batch, src = _select(chap)
                batch.append(chap)
                if len(batch) >= self.storage_batch_size:
                    await _flush(batch, src)

        async def producer() -> None:
            nonlocal completed
            async for cid in self._chapter_ids(vols, start_id, end_id):
                if self.skip_existing and chapter_storage.exists(
                    cid, self.DEFAULT_SOURCE_ID
                ):
                    completed += 1
                    if progress_hook:
                        await progress_hook(completed, total_chapters)
                else:
                    await cid_q.put(cid)

        @asynccontextmanager
        async def task_group_ctx() -> AsyncIterator[None]:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(
                    self._chapter_worker(
                        book_id,
                        ignore_set,
                        cid_q,
                        save_q,
                        sem,
                    )
                )
                tg.create_task(storage_worker(save_q))
                yield

        # run producer + workers, send None sentinels to shut down loops
        async with task_group_ctx():
            await producer()

            # signal fetcher to exit
            await cid_q.put(None)
            await cid_q.join()

            # signal storage to exit
            await save_q.put(None)
            await save_q.join()

            # final flush for both batches
            await _flush(default_batch, self.DEFAULT_SOURCE_ID)
            await _flush(encrypted_batch, self.ENCRYPTED_SOURCE_ID)

        chapter_storage.close()
        self.logger.info(
            "%s Novel '%s' download completed.",
            TAG,
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

    async def _chapter_worker(
        self,
        book_id: str,
        ignore_set: set[str],
        cid_q: asyncio.Queue[str | None],
        save_q: asyncio.Queue[ChapterDict | None],
        sem: asyncio.Semaphore,
    ) -> None:
        """
        Worker that processes one chapter at a time:
        fetch + parse with retry, then enqueue to save_q.
        """
        html_dir = self._debug_dir / book_id / "html"
        while True:
            cid = await cid_q.get()
            if cid is None:
                cid_q.task_done()
                break
            if not cid or cid in ignore_set:
                cid_q.task_done()
                continue

            async with sem:
                chap = await self._process_chapter(book_id, cid, html_dir)
            if chap:
                await save_q.put(chap)

            cid_q.task_done()
            await async_sleep_with_random_delay(
                self.request_interval,
                mul_spread=1.1,
                max_sleep=self.request_interval + 2,
            )

    async def _process_chapter(
        self,
        book_id: str,
        cid: str,
        html_dir: Path,
    ) -> ChapterDict | None:
        """
        Fetch, debug-save, parse a single chapter with retries.
        Returns ChapterDict or None on failure.
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
                    await async_sleep_with_random_delay(
                        base=backoff,
                        mul_spread=1.2,
                        max_sleep=backoff + 3,
                    )
                else:
                    self.logger.warning("[ChapterWorker] Failed %s: %s", cid, e)
        return None
