#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.downloaders.common_asynb_downloader
---------------------------------------------------------

This module defines `CommonAsynbDownloader`.
"""

import asyncio
import json
import logging
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from typing import Any, Dict, Tuple

from novel_downloader.config import DownloaderConfig
from novel_downloader.core.interfaces import (
    AsyncRequesterProtocol,
    ParserProtocol,
    SaverProtocol,
)
from novel_downloader.utils.file_utils import save_as_json, save_as_txt
from novel_downloader.utils.network import download_image_as_bytes
from novel_downloader.utils.time_utils import calculate_time_difference

from .base_async_downloader import BaseAsyncDownloader

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
            success = await self.requester.login(max_retries=3)
            if not success:
                raise RuntimeError("Login failed")
            self._is_logged_in = True

    async def download_one(self, book_id: str) -> None:
        """
        The full download logic for a single book.

        :param book_id: The identifier of the book to download.
        """
        assert isinstance(self.requester, AsyncRequesterProtocol)

        TAG = "[AsyncDownloader]"
        raw_base = self.raw_data_dir / book_id
        cache_base = self.cache_dir / book_id
        info_path = raw_base / "book_info.json"
        chapters_html_dir = cache_base / "html"
        chapter_dir = raw_base / "chapters"

        raw_base.mkdir(parents=True, exist_ok=True)
        chapter_dir.mkdir(parents=True, exist_ok=True)
        if self.save_html:
            chapters_html_dir.mkdir(parents=True, exist_ok=True)

        # load or fetch book_info
        book_info: Dict[str, Any]
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
            info_html = await self.requester.get_book_info(
                book_id, self.request_interval
            )
            if self.save_html:
                save_as_txt(info_html, chapters_html_dir / "info.html")
            book_info = self.parser.parse_book_info(info_html)
            if book_info.get("book_name") != "未找到书名":
                save_as_json(book_info, info_path)
            else:
                logger.warning("%s 书籍信息未找到, book_id = %s", TAG, book_id)
        else:
            book_info = json.loads(info_path.read_text("utf-8"))

        # download cover
        cover_url = book_info.get("cover_url", "")
        if cover_url:
            await asyncio.get_running_loop().run_in_executor(
                None, download_image_as_bytes, cover_url, raw_base
            )

        # setup queue, semaphore, executor
        semaphore = asyncio.Semaphore(self.download_workers)
        queue: asyncio.Queue[Tuple[str, str]] = asyncio.Queue()
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
                        await loop.run_in_executor(
                            executor,
                            save_as_json,
                            chap_json,
                            chapter_dir / f"{cid}.json",
                        )
                        logger.info(
                            "%s [Parser-%d] saved chapter %s", TAG, worker_id, cid
                        )
                except Exception as e:
                    logger.error(
                        "%s [Parser-%d] error on chapter %s: %s", TAG, worker_id, cid, e
                    )
                finally:
                    queue.task_done()

        async def download_worker(chap: Dict[str, Any]) -> None:
            cid = str(chap.get("chapterId") or "")
            if not cid:
                return
            target = chapter_dir / f"{cid}.json"
            if target.exists() and self.skip_existing:
                logger.info("%s skipping existing chapter %s", TAG, cid)
                return

            try:
                async with semaphore:
                    html = await self.requester.get_book_chapter(
                        book_id, cid, self.request_interval
                    )
                if self.save_html:
                    await loop.run_in_executor(
                        executor,
                        save_as_txt,
                        html,
                        chapters_html_dir / f"{cid}.html",
                    )
                await queue.put((cid, html))
                logger.info("%s downloaded chapter %s", TAG, cid)
            except Exception as e:
                logger.error("%s error downloading %s: %s", TAG, cid, e)

        # start parser workers
        parsers = [
            asyncio.create_task(parser_worker(i)) for i in range(self.parser_workers)
        ]

        # enqueue + run downloads
        download_tasks = []
        for vol in book_info.get("volumes", []):
            for chap in vol.get("chapters", []):
                download_tasks.append(asyncio.create_task(download_worker(chap)))

        await asyncio.gather(*download_tasks)
        await queue.join()  # wait until all parsed
        for p in parsers:
            p.cancel()  # stop parser loops

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
