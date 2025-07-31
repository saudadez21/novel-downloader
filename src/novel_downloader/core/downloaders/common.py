#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.common
----------------------------------------

"""

import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from pathlib import Path
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

        book_id = self._normalize_book_id(book_id)

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
        batch: list[ChapterDict] = []
        completed = 0

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
                    await cid_q.put(cid)

        @asynccontextmanager
        async def task_group_ctx() -> AsyncIterator[asyncio.TaskGroup]:
            async with asyncio.TaskGroup() as tg:
                # start chapter workers
                for _ in range(self.workers):
                    tg.create_task(
                        self._chapter_worker(
                            book_id,
                            ignore_set,
                            cid_q,
                            save_q,
                            sem,
                        )
                    )
                # start storage worker
                tg.create_task(storage_worker(save_q))
                yield tg

        # run producer + workers
        async with task_group_ctx():
            # produce all CidTask
            await producer()

            # signal chapter workers to exit
            for _ in range(self.workers):
                await cid_q.put(None)
            await cid_q.join()

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
                    self.logger.info(
                        "[ChapterWorker] Retry %s (%s): %s", cid, attempt + 1, e
                    )
                    backoff = self.backoff_factor * (2**attempt)
                    await async_sleep_with_random_delay(
                        base=backoff, mul_spread=1.2, max_sleep=backoff + 3
                    )
                else:
                    self.logger.warning("[ChapterWorker] Failed %s: %s", cid, e)
        return None

    @staticmethod
    def _normalize_book_id(book_id: str) -> str:
        """
        Normalize a book identifier.

        Subclasses may override this method to transform the book ID
        into their preferred format.
        """
        return book_id.replace("/", "-")
