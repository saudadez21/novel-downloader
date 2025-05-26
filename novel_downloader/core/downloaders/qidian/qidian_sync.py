#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.qidian.qidian_sync
----------------------------------------------------

This module defines `QidianDownloader`, a platform-specific downloader
implementation for retrieving novels from Qidian (起点中文网).
"""

import json
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
from novel_downloader.utils.state import state_mgr
from novel_downloader.utils.time_utils import (
    calculate_time_difference,
    sleep_with_random_delay,
)


class QidianDownloader(BaseDownloader):
    """
    Specialized downloader for Qidian novels.
    """

    def __init__(
        self,
        requester: SyncRequesterProtocol,
        parser: ParserProtocol,
        saver: SaverProtocol,
        config: DownloaderConfig,
    ):
        super().__init__(requester, parser, saver, config, "qidian")

        self._site_key = "qidian"
        self._is_logged_in = self._handle_login()
        state_mgr.set_manual_login_flag(self._site_key, not self._is_logged_in)

    def download_one(self, book_id: str) -> None:
        """
        The full download logic for a single book.

        :param book_id: The identifier of the book to download.
        """
        if not self._is_logged_in:
            self.logger.warning(
                "[%s] login failed, skipping download of %s",
                self._site_key,
                book_id,
            )
            return

        TAG = "[Downloader]"
        save_html = self.config.save_html
        skip_existing = self.config.skip_existing
        wait_time = self.config.request_interval
        scroll = self.config.mode == "browser"

        raw_base = self.raw_data_dir / book_id
        cache_base = self.cache_dir / book_id
        info_path = raw_base / "book_info.json"
        chapters_html_dir = cache_base / "html"

        raw_base.mkdir(parents=True, exist_ok=True)
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

        book_info: dict[str, Any]

        try:
            if not info_path.exists():
                raise FileNotFoundError
            book_info = json.loads(info_path.read_text(encoding="utf-8"))
            days, hrs, mins, secs = calculate_time_difference(
                book_info.get("update_time", ""), "UTC+8"
            )
            self.logger.info(
                "%s Last updated %dd %dh %dm %ds ago", TAG, days, hrs, mins, secs
            )
            if days > 1:
                raise FileNotFoundError  # trigger re-fetch
        except Exception:
            info_html = self.requester.get_book_info(book_id)
            if save_html and info_html:
                info_html_path = chapters_html_dir / "info.html"
                save_as_txt(info_html[0], info_html_path)
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
            self.logger.info("%s Enqueuing volume: %s", TAG, vol_name)

            for chap in vol.get("chapters", []):
                cid = chap.get("chapterId")
                if not cid:
                    self.logger.warning("%s Skipping chapter without chapterId", TAG)
                    continue

                if normal_cs.exists(cid) and skip_existing:
                    self.logger.debug(
                        "%s Chapter already exists, skipping: %s",
                        TAG,
                        cid,
                    )
                    continue

                chap_title = chap.get("title", "")
                self.logger.info("%s Fetching chapter: %s (%s)", TAG, chap_title, cid)
                chap_html = self.requester.get_book_chapter(book_id, cid)
                if not chap_html:
                    continue

                if scroll:
                    self.requester.scroll_page(wait_time * 2)  # type: ignore[attr-defined]
                else:
                    sleep_with_random_delay(
                        wait_time, mul_spread=1.1, max_sleep=wait_time + 2
                    )

                is_encrypted = self.parser.is_encrypted(chap_html[0])  # type: ignore[attr-defined]

                if is_encrypted and encrypted_cs.exists(cid) and skip_existing:
                    self.logger.debug(
                        "%s Chapter already exists, skipping: %s",
                        TAG,
                        cid,
                    )
                    continue

                if save_html and chap_html and not is_vip(chap_html[0]):
                    folder = chapters_html_dir / (
                        "html_encrypted" if is_encrypted else "html_plain"
                    )
                    html_path = folder / f"{cid}.html"
                    save_as_txt(chap_html[0], html_path, on_exist="skip")
                    self.logger.debug(
                        "%s Saved raw HTML for chapter %s to %s", TAG, cid, html_path
                    )

                chap_json = self.parser.parse_chapter(chap_html, cid)
                if not chap_json or not chap_json.get("content"):
                    self.logger.warning(
                        "%s Parsed chapter json is empty, skipping: %s (%s)",
                        TAG,
                        chap_title,
                        cid,
                    )
                    continue

                if is_encrypted:
                    encrypted_cs.save(chap_json)
                else:
                    normal_cs.save(chap_json)
                self.logger.info("%s Saved chapter: %s (%s)", TAG, chap_title, cid)

        normal_cs.close()
        encrypted_cs.close()

        self.saver.save(book_id)

        self.logger.info(
            "%s Novel '%s' download completed.",
            TAG,
            book_info.get("book_name", "unknown"),
        )
        return

    def _handle_login(self) -> bool:
        """
        Perform login with automatic fallback to manual:

        1. If manual_flag is False, try automatic login:
           - On success, return True immediately.
        2. Always attempt manual login if manual_flag is True.
        3. Return True if manual login succeeds, False otherwise.
        """
        manual_flag = state_mgr.get_manual_login_flag(self._site_key)

        # First try automatic login
        if not manual_flag and self._requester.login(manual_login=False):
            return True

        # try manual login
        return self._requester.login(manual_login=True)


def is_vip(html_str: str) -> bool:
    """
    Return True if page indicates VIP-only content.

    :param html_str: Raw HTML string.
    """
    markers = ["这是VIP章节", "需要订阅", "订阅后才能阅读"]
    return any(m in html_str for m in markers)
