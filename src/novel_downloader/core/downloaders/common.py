#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.common
----------------------------------------

"""

import asyncio
import json
from collections.abc import Awaitable, Callable
from contextlib import suppress
from typing import Any, cast

from novel_downloader.core.downloaders.base import BaseDownloader
from novel_downloader.models import (
    BookConfig,
    ChapterDict,
    CidTask,
    HtmlTask,
    RestoreTask,
)
from novel_downloader.utils.chapter_storage import ChapterStorage
from novel_downloader.utils.file_utils import save_as_json, save_as_txt
from novel_downloader.utils.time_utils import (
    async_sleep_with_random_delay,
    calculate_time_difference,
)


class CommonDownloader(BaseDownloader):
    """
    Specialized Async downloader for common novels.
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

        vols = book_info.get("volumes", [])
        total_chapters = 0
        for vol in vols:
            total_chapters += len(vol.get("chapters", []))
        if total_chapters == 0:
            self.logger.warning("%s 书籍没有章节可下载: book_id=%s", TAG, book_id)
            return

        completed_count = 0

        # setup queue, semaphore
        semaphore = asyncio.Semaphore(self.download_workers)
        cid_queue: asyncio.Queue[CidTask] = asyncio.Queue()
        restore_queue: asyncio.Queue[RestoreTask] = asyncio.Queue()
        html_queue: asyncio.Queue[HtmlTask] = asyncio.Queue()
        save_queue: asyncio.Queue[ChapterDict] = asyncio.Queue()
        pending_restore: dict[str, RestoreTask] = {}

        def update_book_info(
            vol_idx: int,
            chap_idx: int,
            cid: str,
        ) -> None:
            try:
                book_info["volumes"][vol_idx]["chapters"][chap_idx]["chapterId"] = cid
            except (IndexError, KeyError, TypeError) as e:
                self.logger.info(
                    "[update_book_info] Failed to update vol=%s, chap=%s: %s",
                    vol_idx,
                    chap_idx,
                    e,
                )

        async def fetcher_worker(
            book_id: str,
            cid_queue: asyncio.Queue[CidTask],
            html_queue: asyncio.Queue[HtmlTask],
            restore_queue: asyncio.Queue[RestoreTask],
            retry_times: int,
            semaphore: asyncio.Semaphore,
        ) -> None:
            while True:
                task = await cid_queue.get()
                cid = task.cid
                if not cid and task.prev_cid:
                    await restore_queue.put(
                        RestoreTask(
                            vol_idx=task.vol_idx,
                            chap_idx=task.chap_idx,
                            prev_cid=task.prev_cid,
                        )
                    )
                    cid_queue.task_done()
                    continue

                if not cid:
                    self.logger.warning("[Fetcher] Skipped empty cid task: %s", task)
                    cid_queue.task_done()
                    continue

                if cid in ignore_set:
                    cid_queue.task_done()
                    continue

                try:
                    async with semaphore:
                        html_list = await self.fetcher.get_book_chapter(book_id, cid)
                    await html_queue.put(
                        HtmlTask(
                            cid=cid,
                            retry=task.retry,
                            html_list=html_list,
                            vol_idx=task.vol_idx,
                            chap_idx=task.chap_idx,
                        )
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
                                prev_cid=task.prev_cid,
                                cid=cid,
                                retry=task.retry + 1,
                                vol_idx=task.vol_idx,
                                chap_idx=task.chap_idx,
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
            worker_id: int,
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
                            "[Parser-%d] saved chapter %s",
                            worker_id,
                            task.cid,
                        )
                    else:
                        raise ValueError("Empty parse result")
                except Exception as e:
                    if task.retry < retry_times:
                        await cid_queue.put(
                            CidTask(
                                prev_cid=None,
                                cid=task.cid,
                                retry=task.retry + 1,
                                vol_idx=task.vol_idx,
                                chap_idx=task.chap_idx,
                            )
                        )
                        self.logger.info(
                            "[Parser-%d] Re-queued cid %s for retry #%d: %s",
                            worker_id,
                            task.cid,
                            task.retry + 1,
                            e,
                        )
                    else:
                        self.logger.warning(
                            "[Parser-%d] Max retries reached for cid %s: %s",
                            worker_id,
                            task.cid,
                            e,
                        )
                finally:
                    html_queue.task_done()

        async def storage_worker(
            cs: ChapterStorage,
            save_queue: asyncio.Queue[ChapterDict],
            restore_queue: asyncio.Queue[RestoreTask],
            cid_queue: asyncio.Queue[CidTask],
        ) -> None:
            nonlocal completed_count
            while True:
                save_task = asyncio.create_task(save_queue.get())
                restore_task = asyncio.create_task(restore_queue.get())

                done, pending = await asyncio.wait(
                    [save_task, restore_task],
                    return_when=asyncio.FIRST_COMPLETED,
                )

                for task in pending:
                    task.cancel()
                    with suppress(asyncio.CancelledError):
                        await task

                for task in done:
                    item = task.result()

                    if isinstance(item, dict):  # from save_queue
                        try:
                            cs.save(cast(ChapterDict, item))
                            completed_count += 1
                            if progress_hook:
                                await progress_hook(completed_count, total_chapters)

                            curr_cid = item["id"]
                            if curr_cid in pending_restore:
                                rt = pending_restore.pop(curr_cid)
                                next_cid = item.get("extra", {}).get("next_chapter_id")
                                if next_cid:
                                    update_book_info(
                                        vol_idx=rt.vol_idx,
                                        chap_idx=rt.chap_idx,
                                        cid=next_cid,
                                    )
                                    await cid_queue.put(
                                        CidTask(
                                            prev_cid=rt.prev_cid,
                                            cid=next_cid,
                                            vol_idx=rt.vol_idx,
                                            chap_idx=rt.chap_idx,
                                        )
                                    )
                                else:
                                    self.logger.warning(
                                        "[storage_worker] No next_cid found for %r",
                                        rt,
                                    )
                        except Exception as e:
                            self.logger.error("[storage_worker] Failed to save: %s", e)
                        finally:
                            save_queue.task_done()

                    elif isinstance(item, RestoreTask):  # from restore_queue
                        prev_json = cs.get(item.prev_cid)
                        next_cid = (
                            prev_json.get("extra", {}).get("next_chapter_id")
                            if prev_json
                            else None
                        )
                        if next_cid:
                            update_book_info(
                                vol_idx=item.vol_idx,
                                chap_idx=item.chap_idx,
                                cid=next_cid,
                            )
                            await cid_queue.put(
                                CidTask(
                                    prev_cid=item.prev_cid,
                                    cid=next_cid,
                                    vol_idx=item.vol_idx,
                                    chap_idx=item.chap_idx,
                                )
                            )
                        else:
                            pending_restore[item.prev_cid] = item
                        restore_queue.task_done()

        fetcher_tasks = [
            asyncio.create_task(
                fetcher_worker(
                    book_id,
                    cid_queue,
                    html_queue,
                    restore_queue,
                    self.retry_times,
                    semaphore,
                )
            )
            for _ in range(self.download_workers)
        ]

        parser_tasks = [
            asyncio.create_task(
                parser_worker(
                    i,
                    cid_queue,
                    html_queue,
                    save_queue,
                    self.retry_times,
                )
            )
            for i in range(self.parser_workers)
        ]

        storage_task = asyncio.create_task(
            storage_worker(
                cs=normal_cs,
                save_queue=save_queue,
                restore_queue=restore_queue,
                cid_queue=cid_queue,
            )
        )

        found_start = start_id is None
        stop_early = False
        last_cid: str | None = None

        for vol_idx, vol in enumerate(vols):
            chapters = vol.get("chapters", [])
            for chap_idx, chap in enumerate(chapters):
                if stop_early:
                    break

                cid = chap.get("chapterId")

                # Skip until reaching start_id
                if not found_start:
                    if cid == start_id:
                        found_start = True
                    else:
                        completed_count += 1
                        last_cid = cid
                        continue

                # Stop when reaching end_id
                if end_id is not None and cid == end_id:
                    stop_early = True

                if cid and normal_cs.exists(cid) and self.skip_existing:
                    completed_count += 1
                    last_cid = cid
                    continue

                await cid_queue.put(
                    CidTask(
                        vol_idx=vol_idx,
                        chap_idx=chap_idx,
                        cid=cid,
                        prev_cid=last_cid,
                    )
                )

                last_cid = cid

            if stop_early:
                break

        await restore_queue.join()
        await cid_queue.join()
        await html_queue.join()
        await save_queue.join()

        for task in fetcher_tasks + parser_tasks + [storage_task]:
            task.cancel()
            with suppress(asyncio.CancelledError):
                await task

        normal_cs.close()
        save_as_json(book_info, info_path)

        self.logger.info(
            "%s Novel '%s' download completed.",
            TAG,
            book_info.get("book_name", "unknown"),
        )
        return
