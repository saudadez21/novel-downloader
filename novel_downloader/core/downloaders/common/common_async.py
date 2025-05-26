#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.common.common_async
-----------------------------------------------------

"""

import asyncio
import json
import logging
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Any

from novel_downloader.config import DownloaderConfig
from novel_downloader.core.downloaders.base import BaseAsyncDownloader
from novel_downloader.core.interfaces import (
    AsyncRequesterProtocol,
    ParserProtocol,
    SaverProtocol,
)
from novel_downloader.utils.chapter_storage import ChapterDict, ChapterStorage
from novel_downloader.utils.file_utils import save_as_json, save_as_txt
from novel_downloader.utils.time_utils import calculate_time_difference

logger = logging.getLogger(__name__)


class CommonAsyncDownloader(BaseAsyncDownloader):
    """
    Specialized Async downloader for common novels.
    """

    def __init__(
        self,
        requester: AsyncRequesterProtocol,
        parser: ParserProtocol,
        saver: SaverProtocol,
        config: DownloaderConfig,
        site: str,
    ):
        """ """
        super().__init__(requester, parser, saver, config, site)
        self._is_logged_in = False

    async def prepare(self) -> None:
        """
        Perform login
        """
        if self.login_required and not self._is_logged_in:
            success = await self.requester.login()
            if not success:
                raise RuntimeError("Login failed")
            self._is_logged_in = True

    async def download_one(self, book_id: str) -> None:
        """
        The full download logic for a single book.

        :param book_id: The identifier of the book to download.
        """
        assert isinstance(self.requester, AsyncRequesterProtocol)
        await self.prepare()

        TAG = "[AsyncDownloader]"
        wait_time = self.config.request_interval

        raw_base = self.raw_data_dir / book_id
        cache_base = self.cache_dir / book_id
        info_path = raw_base / "book_info.json"
        chapters_html_dir = cache_base / "html"

        raw_base.mkdir(parents=True, exist_ok=True)
        if self.save_html:
            chapters_html_dir.mkdir(parents=True, exist_ok=True)
        normal_cs = ChapterStorage(
            raw_base=raw_base,
            namespace="chapters",
            backend_type=self._config.storage_backend,
            batch_size=self._config.storage_batch_size,
        )

        # load or fetch book_info
        book_info: dict[str, Any]
        re_fetch = True
        if info_path.exists():
            try:
                data = json.loads(info_path.read_text("utf-8"))
                days, *_ = calculate_time_difference(
                    data.get("update_time", ""), "UTC+8"
                )
                re_fetch = days > 1
            except Exception:
                re_fetch = True

        if re_fetch:
            info_html = await self.requester.get_book_info(book_id)
            if self.save_html:
                for i, html in enumerate(info_html):
                    save_as_txt(html, chapters_html_dir / f"info_{i}.html")
            book_info = self.parser.parse_book_info(info_html)
            if book_info.get("book_name") != "未找到书名":
                save_as_json(book_info, info_path)
            else:
                logger.warning("%s 书籍信息未找到, book_id = %s", TAG, book_id)
            await asyncio.sleep(wait_time)
        else:
            book_info = json.loads(info_path.read_text("utf-8"))

        # setup queue, semaphore, executor
        semaphore = asyncio.Semaphore(self.download_workers)
        queue: asyncio.Queue[tuple[str, list[str]]] = asyncio.Queue()
        save_queue: asyncio.Queue[ChapterDict] = asyncio.Queue()
        loop = asyncio.get_running_loop()
        executor = (
            ProcessPoolExecutor() if self.use_process_pool else ThreadPoolExecutor()
        )

        async def parser_worker(worker_id: int) -> None:
            while True:
                cid, html = await queue.get()
                try:
                    chap_json = await loop.run_in_executor(
                        executor, self.parser.parse_chapter, html, cid
                    )
                    if chap_json:
                        await save_queue.put(chap_json)
                        logger.info(
                            "%s [Parser-%d] saved chapter %s", TAG, worker_id, cid
                        )
                except Exception as e:
                    logger.error(
                        "%s [Parser-%d] error on chapter %s: %s", TAG, worker_id, cid, e
                    )
                finally:
                    queue.task_done()

        async def saver_loop(
            cs: ChapterStorage,
            queue: asyncio.Queue[ChapterDict],
        ) -> None:
            while True:
                data = await queue.get()
                try:
                    cs.save(data)
                except Exception as e:
                    logger.error(
                        "[saver] Error saving chapter %s: %s",
                        data.get("id"),
                        e,
                    )
                finally:
                    queue.task_done()

        async def download_worker(chap: dict[str, Any]) -> None:
            cid = str(chap.get("chapterId") or "")
            if not cid:
                return
            if normal_cs.exists(cid) and self.skip_existing:
                logger.info("%s skipping existing chapter %s", TAG, cid)
                return

            try:
                async with semaphore:
                    html = await self.requester.get_book_chapter(book_id, cid)
                await queue.put((cid, html))
                logger.info("%s downloaded chapter %s", TAG, cid)
            except Exception as e:
                logger.error("%s error downloading %s: %s", TAG, cid, e)

        # start parser workers
        parsers = [
            asyncio.create_task(parser_worker(i)) for i in range(self.parser_workers)
        ]
        chapter_saver = asyncio.create_task(saver_loop(normal_cs, save_queue))

        # enqueue + run downloads
        download_tasks = []
        for vol in book_info.get("volumes", []):
            for chap in vol.get("chapters", []):
                download_tasks.append(asyncio.create_task(download_worker(chap)))

        await asyncio.gather(*download_tasks)
        await queue.join()  # wait until all parsed
        await save_queue.join()
        for p in parsers:
            p.cancel()  # stop parser loops
        chapter_saver.cancel()

        # final save
        await loop.run_in_executor(executor, self.saver.save, book_id)
        executor.shutdown(wait=True)

        logger.info(
            "%s Novel '%s' download completed.",
            TAG,
            book_info.get("book_name", "unknown"),
        )
        return

    @property
    def parser_workers(self) -> int:
        return self.config.parser_workers

    @property
    def download_workers(self) -> int:
        return self.config.download_workers

    @property
    def use_process_pool(self) -> bool:
        return self.config.use_process_pool
