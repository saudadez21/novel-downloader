#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.qidian
----------------------------------------

"""

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
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

from .tasks import (
    CidTask,
    HtmlTask,
)


@register_downloader(site_keys=["qidian", "qd"])
class QidianDownloader(BaseDownloader):
    """
    Specialized downloader for Qidian novels.
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
        vols = book_info.get("volumes", [])
        total_chapters = sum(len(v.get("chapters", [])) for v in vols)
        if total_chapters == 0:
            self.logger.warning("%s 书籍没有章节可下载: %s", TAG, book_id)
            return

        # queues
        completed = 0
        cid_q: asyncio.Queue[CidTask | None] = asyncio.Queue()
        html_q: asyncio.Queue[HtmlTask | None] = asyncio.Queue()
        save_q: asyncio.Queue[ChapterDict | None] = asyncio.Queue()
        default_batch: list[ChapterDict] = []
        encrypted_batch: list[ChapterDict] = []

        async def _flush_batch(
            batch: list[ChapterDict],
            source_id: int,
        ) -> None:
            nonlocal completed
            if not batch:
                return

            try:
                chapter_storage.upsert_chapters(batch, source_id)
            except Exception as e:
                self.logger.error(
                    "[Storage] batch upsert failed (size=%d, source=%d): %s",
                    len(batch),
                    source_id,
                    e,
                    exc_info=True,
                )
            else:
                completed += len(batch)
                if progress_hook:
                    await progress_hook(completed, total_chapters)
            finally:
                batch.clear()

        def _select_batch_and_source(
            item: ChapterDict,
        ) -> tuple[list[ChapterDict], int]:
            if item.get("extra", {}).get("encrypted", False):
                return encrypted_batch, self.ENCRYPTED_SOURCE_ID
            return default_batch, self.DEFAULT_SOURCE_ID

        async def storage_worker(q: asyncio.Queue[ChapterDict | None]) -> None:
            while True:
                item = await q.get()
                q.task_done()
                if item is None:
                    # final flush before exit
                    if default_batch:
                        await _flush_batch(default_batch, self.DEFAULT_SOURCE_ID)
                    if encrypted_batch:
                        await _flush_batch(encrypted_batch, self.ENCRYPTED_SOURCE_ID)
                    break
                batch, src = _select_batch_and_source(item)
                batch.append(item)
                if len(batch) >= self.storage_batch_size:
                    await _flush_batch(batch, src)

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
                    await cid_q.put(CidTask(cid=cid))

        @asynccontextmanager
        async def worker_group() -> AsyncIterator[None]:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(self._fetcher_worker(book_id, ignore_set, cid_q, html_q))
                tg.create_task(self._parser_worker(book_id, cid_q, html_q, save_q))
                tg.create_task(storage_worker(save_q))
                yield

        # run producer + workers, send None sentinels to shut down loops
        async with worker_group():
            await producer()

            # signal fetcher to exit
            await cid_q.put(None)
            await cid_q.join()

            # signal parser to exit
            await html_q.put(None)
            await html_q.join()

            # signal storage to exit
            await save_q.put(None)
            await save_q.join()

            # final flush for both batches
            await _flush_batch(default_batch, self.DEFAULT_SOURCE_ID)
            await _flush_batch(encrypted_batch, self.ENCRYPTED_SOURCE_ID)

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

    async def _fetcher_worker(
        self,
        book_id: str,
        ignore_set: set[str],
        cid_q: asyncio.Queue[CidTask | None],
        html_q: asyncio.Queue[HtmlTask | None],
    ) -> None:
        while True:
            task = await cid_q.get()
            cid_q.task_done()
            if task is None:
                break
            cid, retry = task.cid, task.retry
            if not cid or cid in ignore_set:
                continue
            try:
                html_list = await self.fetcher.get_book_chapter(book_id, cid)
                await html_q.put(HtmlTask(cid=cid, retry=retry, html_list=html_list))
                self.logger.debug("[Fetcher] Downloaded %s", cid)
                await async_sleep_with_random_delay(
                    self.request_interval,
                    mul_spread=1.1,
                    max_sleep=self.request_interval + 2,
                )
            except Exception as e:
                if retry < self.retry_times:
                    cid_q.put_nowait(CidTask(cid, retry + 1))
                    self.logger.info("[Fetcher] Retry %s (%d): %s", cid, retry + 1, e)
                    backoff = self.backoff_factor * (2**retry)
                    await async_sleep_with_random_delay(
                        base=backoff,
                        mul_spread=1.2,
                        max_sleep=backoff + 3,
                    )
                else:
                    self.logger.warning("[Fetcher] Failed %s: %s", cid, e)

    async def _parser_worker(
        self,
        book_id: str,
        cid_q: asyncio.Queue[CidTask | None],
        html_q: asyncio.Queue[HtmlTask | None],
        save_q: asyncio.Queue[ChapterDict | None],
    ) -> None:
        html_base_dir = self._debug_dir / book_id
        while True:
            task = await html_q.get()
            html_q.task_done()
            if task is None:
                break
            cid, retry, html_list = task.cid, task.retry, task.html_list
            skip_retry = False
            try:
                if self._check_restricted(html_list):
                    self.logger.info("[Parser] Skipped restricted page for %s", cid)
                    skip_retry = True
                    raise ValueError("Restricted content detected")

                is_encrypted = self._check_encrypted(html_list)
                if is_encrypted:
                    skip_retry = True
                folder = "html_encrypted" if is_encrypted else "html_plain"
                self._save_html_pages(
                    html_dir=html_base_dir / folder,
                    filename=cid,
                    html_list=html_list,
                )

                chap = await asyncio.to_thread(
                    self.parser.parse_chapter,
                    html_list,
                    cid,
                )
                if chap:
                    await save_q.put(chap)
                    self.logger.debug("[Parser] Parsed %s", cid)
                else:
                    raise ValueError("Empty parse result")
            except Exception as e:
                if not skip_retry and retry < self.retry_times:
                    cid_q.put_nowait(CidTask(cid, retry + 1))
                    self.logger.info("[Parser] Retry %s (%d): %s", cid, retry + 1, e)
                else:
                    self.logger.warning("[Parser] Failed %s: %s", cid, e)
