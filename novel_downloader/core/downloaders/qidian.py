#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.qidian
----------------------------------------

"""

import asyncio
import json
from contextlib import suppress
from typing import Any, cast

from novel_downloader.core.downloaders.base import BaseDownloader
from novel_downloader.core.interfaces import (
    ExporterProtocol,
    FetcherProtocol,
    ParserProtocol,
)
from novel_downloader.models import (
    ChapterDict,
    CidTask,
    DownloaderConfig,
    HtmlTask,
)
from novel_downloader.utils.chapter_storage import ChapterStorage
from novel_downloader.utils.file_utils import save_as_json, save_as_txt
from novel_downloader.utils.time_utils import (
    async_sleep_with_random_delay,
    calculate_time_difference,
)


class QidianDownloader(BaseDownloader):
    """
    Specialized downloader for Qidian novels.
    """

    def __init__(
        self,
        fetcher: FetcherProtocol,
        parser: ParserProtocol,
        exporter: ExporterProtocol,
        config: DownloaderConfig,
    ):
        super().__init__(fetcher, parser, exporter, config, "qidian")

    async def _download_one(self, book_id: str) -> None:
        """
        The full download logic for a single book.

        :param book_id: The identifier of the book to download.
        """
        TAG = "[Downloader]"

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
        encrypted_cs = ChapterStorage(
            raw_base=raw_base,
            namespace="encrypted_chapters",
            backend_type=self._config.storage_backend,
            batch_size=self._config.storage_batch_size,
        )

        # load or fetch book_info
        book_info: dict[str, Any]
        re_fetch = True
        old_data: dict[str, Any] = {}

        if info_path.exists():
            try:
                old_data = json.loads(info_path.read_text("utf-8"))
                days, *_ = calculate_time_difference(
                    old_data.get("update_time", ""), "UTC+8"
                )
                re_fetch = days > 1
            except Exception:
                re_fetch = True

        if re_fetch:
            info_html = await self.fetcher.get_book_info(book_id)
            if self.save_html:
                for i, html in enumerate(info_html):
                    save_as_txt(html, chapters_html_dir / f"info_{i}.html")
            book_info = self.parser.parse_book_info(info_html)

            if book_info.get("book_name") != "未找到书名":
                save_as_json(book_info, info_path)
            else:
                self.logger.warning("%s 书籍信息未找到, book_id = %s", TAG, book_id)
                book_info = old_data or {"book_name": "未找到书名"}
        else:
            book_info = old_data

        # setup queue
        cid_queue: asyncio.Queue[CidTask] = asyncio.Queue()
        html_queue: asyncio.Queue[HtmlTask] = asyncio.Queue()
        save_queue: asyncio.Queue[ChapterDict] = asyncio.Queue()

        async def fetcher_worker(
            book_id: str,
            cid_queue: asyncio.Queue[CidTask],
            html_queue: asyncio.Queue[HtmlTask],
            retry_times: int,
        ) -> None:
            while True:
                task = await cid_queue.get()
                cid = task.cid
                if not cid:
                    self.logger.warning("[Fetcher] Skipped empty cid task: %s", task)
                    cid_queue.task_done()
                    continue

                try:
                    html_list = await self.fetcher.get_book_chapter(book_id, cid)
                    await html_queue.put(
                        HtmlTask(cid=cid, retry=task.retry, html_list=html_list)
                    )
                    self.logger.info("[Fetcher] Downloaded chapter %s", cid)
                    await async_sleep_with_random_delay(
                        self.request_interval,
                        mul_spread=1.1,
                        max_sleep=self.request_interval + 2,
                    )

                except Exception as e:
                    if task.retry < retry_times:
                        await cid_queue.put(
                            CidTask(
                                prev_cid=task.prev_cid, cid=cid, retry=task.retry + 1
                            )
                        )
                        self.logger.info(
                            "[Fetcher] Re-queued chapter %s for retry #%d: %s",
                            cid,
                            task.retry + 1,
                            e,
                        )
                        backoff = self.backoff_factor * (2**task.retry)
                        await async_sleep_with_random_delay(
                            base=backoff,
                            mul_spread=1.2,
                            max_sleep=backoff + 3,
                        )
                    else:
                        self.logger.warning(
                            "[Fetcher] Max retries reached for chapter %s: %s",
                            cid,
                            e,
                        )

                finally:
                    cid_queue.task_done()

        async def parser_worker(
            cid_queue: asyncio.Queue[CidTask],
            html_queue: asyncio.Queue[HtmlTask],
            save_queue: asyncio.Queue[ChapterDict],
            retry_times: int,
        ) -> None:
            while True:
                task = await html_queue.get()
                try:
                    chap_json = await asyncio.to_thread(
                        self.parser.parse_chapter,
                        task.html_list,
                        task.cid,
                    )
                    if chap_json:
                        await save_queue.put(chap_json)
                        self.logger.info(
                            "[Parser] saved chapter %s",
                            task.cid,
                        )
                        if self.save_html:
                            is_encrypted = chap_json.get("extra", {}).get(
                                "encrypted", False
                            )
                            folder = chapters_html_dir / (
                                "html_encrypted" if is_encrypted else "html_plain"
                            )
                            html_path = folder / f"{cid}.html"
                            save_as_txt(task.html_list[0], html_path, on_exist="skip")
                            self.logger.debug(
                                "%s Saved raw HTML for chapter %s to %s",
                                TAG,
                                cid,
                                html_path,
                            )
                    else:
                        raise ValueError("Empty parse result")
                except Exception as e:
                    if task.retry < retry_times:
                        await cid_queue.put(
                            CidTask(prev_cid=None, cid=task.cid, retry=task.retry + 1)
                        )
                        self.logger.info(
                            "[Parser] Re-queued cid %s for retry #%d: %s",
                            task.cid,
                            task.retry + 1,
                            e,
                        )
                    else:
                        self.logger.warning(
                            "[Parser] Max retries reached for cid %s: %s",
                            task.cid,
                            e,
                        )
                finally:
                    html_queue.task_done()

        async def storage_worker(
            normal_cs: ChapterStorage,
            encrypted_cs: ChapterStorage,
            save_queue: asyncio.Queue[ChapterDict],
        ) -> None:
            while True:
                item = await save_queue.get()
                try:
                    is_encrypted = item.get("extra", {}).get("encrypted", False)
                    cs = encrypted_cs if is_encrypted else normal_cs
                    cs.save(cast(ChapterDict, item))
                    cs.save(cast(ChapterDict, item))
                except Exception as e:
                    self.logger.error("[storage_worker] Failed to save: %s", e)
                finally:
                    save_queue.task_done()

        fetcher_task = asyncio.create_task(
            fetcher_worker(
                book_id,
                cid_queue,
                html_queue,
                self.retry_times,
            )
        )

        parser_task = asyncio.create_task(
            parser_worker(
                cid_queue,
                html_queue,
                save_queue,
                self.retry_times,
            )
        )

        storage_task = asyncio.create_task(
            storage_worker(
                normal_cs=normal_cs,
                encrypted_cs=encrypted_cs,
                save_queue=save_queue,
            )
        )

        last_cid: str | None = None
        for vol in book_info.get("volumes", []):
            chapters = vol.get("chapters", [])
            for chap in chapters:
                cid = chap.get("chapterId")
                if cid and normal_cs.exists(cid) and self.skip_existing:
                    last_cid = cid
                    continue

                await cid_queue.put(CidTask(cid=cid, prev_cid=last_cid))
                last_cid = cid

        await cid_queue.join()
        await html_queue.join()
        await save_queue.join()

        for task in [fetcher_task, parser_task, storage_task]:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

        normal_cs.close()
        encrypted_cs.close()

        await asyncio.to_thread(self.exporter.export, book_id)

        self.logger.info(
            "%s Novel '%s' download completed.",
            TAG,
            book_info.get("book_name", "unknown"),
        )
        return
