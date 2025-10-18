#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n69yue.parser
--------------------------------------------

"""

import json
import logging
from typing import Any

from lxml import html

from novel_downloader.infra.paths import N69YUE_MAP_PATH
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
class N69yueParser(BaseParser):
    """
    Parser for 69阅读 book pages.
    """

    site_name: str = "n69yue"
    BASE_URL = "https://www.69yue.top"

    _FONT_MAP: dict[str, str] = {}

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if len(html_list) < 2:
            return None

        info_tree = html.fromstring(html_list[0])
        catalog_data = json.loads(html_list[1])
        use_font = self._has_fonts(html_list[0])

        # --- base info ---
        book_name = self._first_str(info_tree.xpath("//h1/text()"))
        cover_src = self._first_str(
            info_tree.xpath("//img[contains(@class, 'object-cover')]/@src")
        )
        cover_url = self.BASE_URL + cover_src if cover_src else ""
        serial_status = self._first_str(
            info_tree.xpath("//p[contains(., '状态')]/span/text()"),
            replaces=[("状态：", "")],
        )
        word_count = self._first_str(
            info_tree.xpath("//p[contains(., '字数')]/text()"),
            replaces=[("字数：", "")],
        )
        update_time = self._first_str(
            info_tree.xpath("//p[contains(., '更新')]/text()"),
            replaces=[("更新：", "")],
        )
        tags = list(
            {
                self._first_str([x])
                for x in info_tree.xpath("//div[@class='tags-container']//span/text()")
            }
        )
        summary = self._join_strs(
            info_tree.xpath("//div[contains(@class, 'summary')]/text()")
        )

        if use_font:
            book_name = self._map_fonts(book_name)
            serial_status = self._map_fonts(serial_status)
            word_count = self._map_fonts(word_count)
            update_time = self._map_fonts(update_time)
            tags = [self._map_fonts(t) for t in tags]
            summary = self._map_fonts(summary)

        # --- Chapter volumes & listings ---
        items = catalog_data.get("items", [])
        chapters: list[ChapterInfoDict] = []
        for item in reversed(items):
            title = item.get("cn", "").strip()
            cid = item.get("cid", "").strip()
            if use_font:
                title = self._map_fonts(title)
            chapters.append(
                {
                    "title": title,
                    "url": f"/article/{cid}.html",
                    "chapterId": cid,
                }
            )

        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": "",
            "cover_url": cover_url,
            "serial_status": serial_status,
            "word_count": word_count,
            "update_time": update_time,
            "tags": tags,
            "summary": summary,
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
            return None

        tree = html.fromstring(html_list[0])

        title = self._first_str(
            tree.xpath("//main[contains(@class,'reading-container')]//h2/text()")
        )

        paragraphs: list[str] = []
        for article in tree.xpath(
            "//article[contains(@class,'reading-content')]/article"
        ):
            self._extract_node(article, paragraphs)

        if not paragraphs:
            return None
        if paragraphs[0].strip() == title.strip():
            paragraphs.pop(0)

        if not paragraphs:
            return None
        last = paragraphs[-1].rstrip()
        if last.endswith("(本章完)"):
            last = last[: -len("(本章完)")].rstrip()
            if last:
                paragraphs[-1] = last
            else:
                paragraphs.pop()

        if not paragraphs:
            return None

        content = "\n".join(paragraphs)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }

    @classmethod
    def _map_fonts(cls, text: str) -> str:
        """
        Apply font mapping to the input text.
        """
        if not cls._FONT_MAP:
            cls._FONT_MAP = json.loads(N69YUE_MAP_PATH.read_text(encoding="utf-8"))

        return "".join(cls._FONT_MAP.get(c, c) for c in text)

    @staticmethod
    def _has_fonts(html_str: str) -> bool:
        """
        Determine whether HTML content likely uses obfuscated fonts.
        """
        obfuscated = "/static/assets/css/style.css" in html_str
        if obfuscated and "/static/assets/css/style.css?ver=20250901" not in html_str:
            logger.warning(
                "n69yue parser: detected potential obfuscated fonts - "
                "script version mismatch. "
                "This may cause incorrect character decoding. "
                "Please report this issue so the handler can be updated."
            )
        return obfuscated

    def _extract_node(self, node: html.HtmlElement, paragraphs: list[str]) -> None:
        if node.text and (line := node.text.strip()):
            paragraphs.append(line)

        for child in node:
            self._extract_node(child, paragraphs)

            if child.tail and (line := child.tail.strip()):
                paragraphs.append(line)
