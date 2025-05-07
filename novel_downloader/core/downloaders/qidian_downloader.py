#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.downloaders.qidian_downloader
---------------------------------------------------

This module defines `QidianDownloader`, a platform-specific downloader
implementation for retrieving novels from Qidian (起点中文网).
"""

import json
import logging
from typing import Any, Dict

from novel_downloader.config import DownloaderConfig
from novel_downloader.core.interfaces import (
    ParserProtocol,
    RequesterProtocol,
    SaverProtocol,
)
from novel_downloader.utils.file_utils import save_as_json, save_as_txt
from novel_downloader.utils.network import download_image_as_bytes
from novel_downloader.utils.state import state_mgr
from novel_downloader.utils.time_utils import calculate_time_difference

from .base_downloader import BaseDownloader

logger = logging.getLogger(__name__)


class QidianDownloader(BaseDownloader):
    """
    Specialized downloader for Qidian novels.
    """

    def __init__(
        self,
        requester: RequesterProtocol,
        parser: ParserProtocol,
        saver: SaverProtocol,
        config: DownloaderConfig,
    ):
        super().__init__(requester, parser, saver, config)

        self._site_key = "qidian"
        self._is_logged_in = self._handle_login()
        state_mgr.set_manual_login_flag(self._site_key, not self._is_logged_in)

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
        if not manual_flag:
            if self._requester.login(manual_login=False):
                return True

        # try manual login
        return self._requester.login(manual_login=True)

    def download_one(self, book_id: str) -> None:
        """
        The full download logic for a single book.

        :param book_id: The identifier of the book to download.
        """
        if not self._is_logged_in:
            logger.warning(
                f"[{self._site_key}] login failed, skipping download of {book_id}"
            )
            return

        TAG = "[Downloader]"
        save_html = self.config.save_html
        skip_existing = self.config.skip_existing
        wait_time = self.config.request_interval

        raw_base = self.raw_data_dir / "qidian" / book_id
        cache_base = self.cache_dir / "qidian" / book_id
        info_path = raw_base / "book_info.json"
        chapter_dir = raw_base / "chapters"
        encrypted_chapter_dir = raw_base / "encrypted_chapters"
        if save_html:
            chapters_html_dir = cache_base / "html"

        raw_base.mkdir(parents=True, exist_ok=True)
        chapter_dir.mkdir(parents=True, exist_ok=True)
        encrypted_chapter_dir.mkdir(parents=True, exist_ok=True)

        book_info: Dict[str, Any]

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
            info_html = self.requester.get_book_info(book_id, wait_time)
            if save_html:
                info_html_path = chapters_html_dir / "info.html"
                save_as_txt(info_html, info_html_path)
            book_info = self.parser.parse_book_info(info_html)
            if (
                book_info.get("book_name", "") != "未找到书名"
                and book_info.get("update_time", "") != "未找到更新时间"
            ):
                save_as_json(book_info, info_path)

        # download cover
        cover_url = book_info.get("cover_url", "")
        if cover_url:
            cover_bytes = download_image_as_bytes(cover_url, raw_base)
            if not cover_bytes:
                logger.warning("%s Failed to download cover: %s", TAG, cover_url)

        # enqueue chapters
        for vol in book_info.get("volumes", []):
            vol_name = vol.get("volume_name", "")
            logger.info("%s Enqueuing volume: %s", TAG, vol_name)

            for chap in vol.get("chapters", []):
                cid = chap.get("chapterId")
                if not cid:
                    logger.warning("%s Skipping chapter without chapterId", TAG)
                    continue

                chap_path = chapter_dir / f"{cid}.json"

                if chap_path.exists() and skip_existing:
                    logger.debug(
                        "%s Chapter already exists, skipping: %s",
                        TAG,
                        cid,
                    )
                    continue

                chap_title = chap.get("title", "")
                logger.info("%s Fetching chapter: %s (%s)", TAG, chap_title, cid)
                chap_html = self.requester.get_book_chapter(book_id, cid, wait_time)

                is_encrypted = self.parser.is_encrypted(chap_html)  # type: ignore[attr-defined]

                folder = encrypted_chapter_dir if is_encrypted else chapter_dir
                chap_path = folder / f"{cid}.json"

                if chap_path.exists() and skip_existing:
                    logger.debug(
                        "%s Chapter already exists, skipping: %s",
                        TAG,
                        cid,
                    )
                    continue

                if save_html and not is_vip(chap_html):
                    folder = chapters_html_dir / (
                        "html_encrypted" if is_encrypted else "html_plain"
                    )
                    html_path = folder / f"{cid}.html"
                    save_as_txt(chap_html, html_path, on_exist="skip")
                    logger.debug(
                        "%s Saved raw HTML for chapter %s to %s", TAG, cid, html_path
                    )

                chap_json = self.parser.parse_chapter(chap_html, cid)
                if not chap_json:
                    logger.warning(
                        "%s Parsed chapter json is empty, skipping: %s (%s)",
                        TAG,
                        chap_title,
                        cid,
                    )
                    continue

                save_as_json(chap_json, chap_path)
                logger.info("%s Saved chapter: %s (%s)", TAG, chap_title, cid)

        self.saver.save(book_id)

        logger.info(
            "%s Novel '%s' download completed.",
            TAG,
            book_info.get("book_name", "unknown"),
        )
        return


def is_vip(html_str: str) -> bool:
    """
    Return True if page indicates VIP-only content.

    :param html_str: Raw HTML string.
    """
    markers = ["这是VIP章节", "需要订阅", "订阅后才能阅读"]
    return any(m in html_str for m in markers)
