#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ciyuanji.parser
----------------------------------------------
"""

import json
import logging
from base64 import b64decode
from collections import defaultdict
from typing import Any

from Crypto.Cipher import DES
from Crypto.Util.Padding import unpad
from lxml import html

from novel_downloader.plugins.base.parser import BaseParser
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import (
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    VolumeInfoDict,
)

logger = logging.getLogger(__name__)


@registrar.register_parser()
class CiyuanjiParser(BaseParser):
    """
    Parser for 次元姬 book pages.
    """

    site_name: str = "ciyuanji"
    BASE_URL = "https://www.ciyuanji.com"
    _CHAPTER_KEY = b"ZUreQN0E"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        data = self._find_next_data(html_list[0])
        if not data:
            logger.warning("ciyuanji book_info: __NEXT_DATA__ not found")
            return None

        book_data = self._extract_book_data(data)
        raw_chapters = self._extract_chapter_list(data)
        volumes = self._build_volumes(raw_chapters)
        tags = [t["tagName"] for t in book_data.get("tagList", []) if "tagName" in t]

        return {
            "book_name": book_data.get("bookName", ""),
            "author": book_data.get("authorName", ""),
            "cover_url": book_data.get("imgUrl", ""),
            "update_time": book_data.get("latestUpdateTime", ""),
            "word_count": str(book_data.get("wordCount", "")),
            "serial_status": self._map_serial_status(book_data.get("endState")),
            "summary": book_data.get("notes", ""),
            "tags": tags,
            "volumes": volumes,
            "extra": {},
        }

    def parse_chapter(
        self,
        html_list: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        if not html_list:
            logger.warning("ciyuanji chapter %s: html_list is empty", chapter_id)
            return None

        if self._check_login(html_list[0]):
            logger.warning("ciyuanji chapter %s: VIP login required", chapter_id)
            return None

        if self._check_unlock(html_list[0]):
            logger.warning("ciyuanji chapter %s: locked (need purchase)", chapter_id)
            return None

        data = self._find_next_data(html_list[0])
        if not data:
            logger.warning("ciyuanji chapter %s: __NEXT_DATA__ not found", chapter_id)
            return None

        chapter_content = self._extract_chapter_content(data)
        if not chapter_content:
            logger.warning("ciyuanji chapter %s: chapterContent not found", chapter_id)
            return None

        content_enc = chapter_content.get("content", "")
        if not content_enc:
            logger.warning("ciyuanji chapter %s: no encrypted content", chapter_id)
            return None

        # Try to decrypt
        content = self._decrypt_chapter(content_enc)

        # Build result
        return {
            "id": str(chapter_content.get("chapterId", chapter_id)),
            "title": chapter_content.get("chapterName", ""),
            "content": content,
            "extra": chapter_content,
        }

    def _build_volumes(
        self, chapter_list: list[dict[str, Any]]
    ) -> list[VolumeInfoDict]:
        """
        Build structured volumes + chapters from raw chapter list.
        Groups by volumeId, sorts volumes and chapters.
        """
        if not chapter_list:
            return []

        grouped: dict[int, dict[str, Any]] = defaultdict(lambda: {"chapters": []})

        for ch in chapter_list:
            volume_id = ch.get("volumeId")
            if not volume_id:
                continue
            volume_title = ch.get("title", f"卷 {volume_id}")
            volume_sort = ch.get("volumeSortNum", 0)

            # Build individual chapter entry
            chapter_info: ChapterInfoDict = {
                "title": ch.get("chapterName", ""),
                "url": f"/chapter/{ch.get('bookId')}_{ch.get('chapterId')}.html",
                "chapterId": str(ch.get("chapterId")),
                "accessible": ch.get("isFee", "0") == "0"
                or ch.get("isBuy", "0") == "1",
            }

            vol = grouped[volume_id]
            vol["volume_name"] = volume_title
            vol["volumeSortNum"] = volume_sort
            vol["chapters"].append((ch.get("sortNum", 0), chapter_info))

        # Sort volumes by volumeSortNum
        sorted_volumes = sorted(
            grouped.values(), key=lambda v: v.get("volumeSortNum", 0)
        )

        # Build final structured list
        volumes: list[VolumeInfoDict] = []
        for vol in sorted_volumes:
            chapters_sorted = [
                ci for _, ci in sorted(vol["chapters"], key=lambda x: x[0])
            ]
            volumes.append(
                {
                    "volume_name": vol["volume_name"],
                    "chapters": chapters_sorted,
                }
            )

        return volumes

    @staticmethod
    def _map_serial_status(status: str | int | None) -> str:
        """
        Map endState value to human-readable Chinese status.
        """
        if status is None:
            return ""
        status_str = str(status)
        mapping = {
            "1": "完结",
            "2": "连载",
        }
        return mapping.get(status_str, status_str)

    @staticmethod
    def _find_next_data(html_str: str) -> dict[str, Any]:
        """
        Extract SSR JSON from <script id="__NEXT_DATA__">.
        """
        tree = html.fromstring(html_str)
        script = tree.xpath('//script[@id="__NEXT_DATA__"]/text()')
        return json.loads(script[0].strip()) if script else {}

    @staticmethod
    def _extract_book_data(data: dict[str, Any]) -> dict[str, Any]:
        props = data.get("props", {})
        page_props = props.get("pageProps", {})
        book_data = page_props.get("book", {})
        return book_data if isinstance(book_data, dict) else {}

    @staticmethod
    def _extract_chapter_list(data: dict[str, Any]) -> list[dict[str, Any]]:
        props = data.get("props", {})
        page_props = props.get("pageProps", {})
        book_chapter = page_props.get("bookChapter", {})
        chapter_list = book_chapter.get("chapterList", [])
        return chapter_list if isinstance(chapter_list, list) else []

    @staticmethod
    def _extract_chapter_content(data: dict[str, Any]) -> dict[str, Any]:
        props = data.get("props", {})
        page_props = props.get("pageProps", {})
        chapter_content = page_props.get("chapterContent", {})
        return chapter_content if isinstance(chapter_content, dict) else {}

    @staticmethod
    def _check_login(html_str: str) -> bool:
        keywords = {
            "其他登录方式",
            "注册&amp;登录",
        }
        return any(kw in html_str for kw in keywords)

    @staticmethod
    def _check_unlock(html_str: str) -> bool:
        return "需订阅后才能阅读" in html_str

    @classmethod
    def _decrypt_chapter(cls, content: str) -> str:
        content = content.replace("\n", "")
        ciphertext = b64decode(content)
        cipher = DES.new(cls._CHAPTER_KEY, DES.MODE_ECB)
        plaintext: str = unpad(cipher.decrypt(ciphertext), 8).decode("utf-8")
        return plaintext
