#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.common
----------------------------------------

"""

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any

from novel_downloader.core.downloaders.base import BaseDownloader
from novel_downloader.models import (
    BookConfig,
    ChapterDict,
)
from novel_downloader.utils import (
    ChapterStorage,
    async_sleep_with_random_delay,
)

from .tasks import (
    CidTask,
    HtmlTask,
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

        # prepare storage & dirs
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

        # queues & semaphore
        completed = 0
        sem = asyncio.Semaphore(self.download_workers)
        cid_q: asyncio.Queue[CidTask | None] = asyncio.Queue()
        html_q: asyncio.Queue[HtmlTask | None] = asyncio.Queue()
        save_q: asyncio.Queue[ChapterDict | None] = asyncio.Queue()
        batch: list[ChapterDict] = []

        async def _flush_batch() -> None:
            nonlocal batch, completed
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
                completed += len(batch)
                if progress_hook:
                    await progress_hook(completed, total_chapters)
            finally:
                batch.clear()

        async def storage_worker(q: asyncio.Queue[ChapterDict | None]) -> None:
            while True:
                item = await q.get()
                q.task_done()
                if item is None:
                    # final flush before exit
                    if batch:
                        await _flush_batch()
                    break
                batch.append(item)
                if len(batch) >= self.storage_batch_size:
                    await _flush_batch()

        async def producer() -> None:
            nonlocal completed
            async for cid in self._chapter_ids(vols, start_id, end_id):
                if self.skip_existing and chapter_storage.exists(cid):
                    completed += 1
                    if progress_hook:
                        await progress_hook(completed, total_chapters)
                else:
                    await cid_q.put(CidTask(cid=cid))

        def start_workers(group: asyncio.TaskGroup) -> None:
            # fetcher workers
            for _ in range(self.download_workers):
                group.create_task(
                    self._fetcher_worker(book_id, ignore_set, cid_q, html_q, sem)
                )
            # parser workers
            for i in range(self.parser_workers):
                group.create_task(
                    self._parser_worker(i, book_id, cid_q, html_q, save_q)
                )
            # single storage worker
            group.create_task(storage_worker(save_q))

        @asynccontextmanager
        async def task_group_ctx() -> AsyncIterator[asyncio.TaskGroup]:
            async with asyncio.TaskGroup() as tg:
                start_workers(tg)
                yield tg

        # run everything, sending None sentinels to shut down infinite loops
        async with task_group_ctx():
            # produce all CidTask
            await producer()

            # signal fetchers to exit and wait
            for _ in range(self.download_workers):
                await cid_q.put(None)
            await cid_q.join()

            # signal parser workers to exit
            for _ in range(self.parser_workers):
                await html_q.put(None)
            await html_q.join()

            # signal storage worker to exit
            await save_q.put(None)
            await save_q.join()

            # final flush to catch any remaining items
            await _flush_batch()

        chapter_storage.close()
        self.logger.info(
            "%s Novel '%s' download completed.",
            TAG,
            book_info.get("book_name", "unknown"),
        )

    async def _fetcher_worker(
        self,
        book_id: str,
        ignore_set: set[str],
        cid_q: asyncio.Queue[CidTask | None],
        html_q: asyncio.Queue[HtmlTask | None],
        sem: asyncio.Semaphore,
    ) -> None:
        while True:
            task = await cid_q.get()
            if task is None:
                cid_q.task_done()
                break

            cid, retry = task.cid, task.retry
            if not cid or cid in ignore_set:
                cid_q.task_done()
                continue

            try:
                async with sem:
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
                        base=backoff, mul_spread=1.2, max_sleep=backoff + 3
                    )
                else:
                    self.logger.warning("[Fetcher] Failed %s: %s", cid, e)
            finally:
                cid_q.task_done()

    async def _parser_worker(
        self,
        worker_id: int,
        book_id: str,
        cid_q: asyncio.Queue[CidTask | None],
        html_q: asyncio.Queue[HtmlTask | None],
        save_q: asyncio.Queue[ChapterDict | None],
    ) -> None:
        html_dir = self._debug_dir / book_id / "html"
        while True:
            task = await html_q.get()
            if task is None:
                html_q.task_done()
                break

            cid, retry, html_list = task.cid, task.retry, task.html_list
            try:
                self._save_html_pages(html_dir, cid, html_list)
                chap = await asyncio.to_thread(
                    self.parser.parse_chapter, html_list, cid
                )
                if chap:
                    await save_q.put(chap)
                    self.logger.debug("[Parser-%d] Parsed %s", worker_id, cid)
                else:
                    raise ValueError("Empty parse result")
            except Exception as e:
                if retry < self.retry_times:
                    cid_q.put_nowait(CidTask(cid, retry + 1))
                    self.logger.info(
                        "[Parser-%d] Retry %s (%d): %s", worker_id, cid, retry + 1, e
                    )
                else:
                    self.logger.warning("[Parser-%d] Failed %s: %s", worker_id, cid, e)
            finally:
                html_q.task_done()
