#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.common.common_sync
----------------------------------------------------

This module defines `CommonDownloader`.
"""

import json
import logging
from typing import Any

from novel_downloader.config import DownloaderConfig
from novel_downloader.core.downloaders.base import BaseDownloader
from novel_downloader.core.interfaces import (
    ParserProtocol,
    SaverProtocol,
    SyncRequesterProtocol,
)
from novel_downloader.utils.chapter_storage import ChapterStorage
from novel_downloader.utils.file_utils import save_as_json, save_as_txt
from novel_downloader.utils.time_utils import (
    calculate_time_difference,
    sleep_with_random_delay,
)

logger = logging.getLogger(__name__)


class CommonDownloader(BaseDownloader):
    """
    Specialized downloader for common novels.
    """

    def __init__(
        self,
        requester: SyncRequesterProtocol,
        parser: ParserProtocol,
        saver: SaverProtocol,
        config: DownloaderConfig,
        site: str,
    ):
        """
        Initialize the common novel downloader with site information.

        :param requester: Object implementing RequesterProtocol, used to fetch raw data.
        :param parser: Object implementing ParserProtocol, used to parse page content.
        :param saver: Object implementing SaverProtocol, used to save final output.
        :param config: Downloader configuration object.
        :param site: Identifier for the site the downloader is targeting.
        """
        super().__init__(requester, parser, saver, config, site)
        self._site = site
        self._is_logged_in = False

    def prepare(self) -> None:
        """
        Perform login
        """
        if self.login_required and not self._is_logged_in:
            success = self.requester.login()
            if not success:
                raise RuntimeError("Login failed")
            self._is_logged_in = True

    def download_one(self, book_id: str) -> None:
        """
        The full download logic for a single book.

        :param book_id: The identifier of the book to download.
        """
        self.prepare()

        TAG = "[Downloader]"
        save_html = self.config.save_html
        skip_existing = self.config.skip_existing
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

        book_info: dict[str, Any]

        try:
            if not info_path.exists():
                raise FileNotFoundError
            book_info = json.loads(info_path.read_text(encoding="utf-8"))
            days, hrs, mins, secs = calculate_time_difference(
                book_info.get("update_time", ""), "UTC+8"
            )
            logger.info(
                "%s Last updated %dd %dh %dm %ds ago", TAG, days, hrs, mins, secs
            )
            if days > 1:
                raise FileNotFoundError  # trigger re-fetch
        except Exception:
            info_html = self.requester.get_book_info(book_id)
            if save_html:
                for i, html in enumerate(info_html):
                    save_as_txt(html, chapters_html_dir / f"info_{i}.html")
            book_info = self.parser.parse_book_info(info_html)
            if (
                book_info.get("book_name", "") != "未找到书名"
                and book_info.get("update_time", "") != "未找到更新时间"
            ):
                save_as_json(book_info, info_path)
            sleep_with_random_delay(wait_time, mul_spread=1.1, max_sleep=wait_time + 2)

        # enqueue chapters
        for vol in book_info.get("volumes", []):
            vol_name = vol.get("volume_name", "")
            logger.info("%s Enqueuing volume: %s", TAG, vol_name)

            for chap in vol.get("chapters", []):
                cid = chap.get("chapterId")
                if not cid:
                    logger.warning("%s Skipping chapter without chapterId", TAG)
                    continue

                if normal_cs.exists(cid) and skip_existing:
                    logger.debug(
                        "%s Chapter already exists, skipping: %s",
                        TAG,
                        cid,
                    )
                    continue

                chap_title = chap.get("title", "")
                logger.info("%s Fetching chapter: %s (%s)", TAG, chap_title, cid)
                try:
                    chap_html = self.requester.get_book_chapter(book_id, cid)

                    if save_html:
                        for i, html in enumerate(chap_html):
                            html_path = chapters_html_dir / f"{cid}_{i}.html"
                            save_as_txt(html, html_path, on_exist="skip")

                    chap_json = self.parser.parse_chapter(chap_html, cid)

                    sleep_with_random_delay(
                        wait_time, mul_spread=1.1, max_sleep=wait_time + 2
                    )
                    if not chap_json:
                        logger.warning(
                            "%s Parsed chapter json is empty, skipping: %s (%s)",
                            TAG,
                            chap_title,
                            cid,
                        )
                        continue
                except Exception as e:
                    logger.warning(
                        "%s Error while processing chapter %s (%s): %s",
                        TAG,
                        chap_title,
                        cid,
                        str(e),
                    )
                    continue

                normal_cs.save(chap_json)
                logger.info("%s Saved chapter: %s (%s)", TAG, chap_title, cid)

        normal_cs.close()
        self.saver.save(book_id)

        logger.info(
            "%s Novel '%s' download completed.",
            TAG,
            book_info.get("book_name", "unknown"),
        )
        return

    @property
    def site(self) -> str:
        """
        Get the site identifier.

        :return: The site string.
        """
        return self._site

    @site.setter
    def site(self, value: str) -> None:
        """
        Set the site identifier.

        :param value: New site string to set.
        """
        self._site = value
