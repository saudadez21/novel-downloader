#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.yodu.parser
------------------------------------------

"""

import json
import re
from typing import Any

from lxml import html

from novel_downloader.infra.paths import YODU_MAP_PATH
from novel_downloader.plugins.base.parser import BaseParser
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import (
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    VolumeInfoDict,
)


@registrar.register_parser()
class YoduParser(BaseParser):
    """
    Parser for 有度中文网 book pages.
    """

    site_name: str = "yodu"

    _NEXTPAGE_RE = re.compile(r'nextpage="/book/\d+/(\d+)\.html"')
    _FONT_MAP: dict[str, str] = {}

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        # --- Metadata ---
        book_name = (
            self._first_str(
                tree.xpath('//meta[@property="og:novel:book_name"]/@content')
            )
            or self._first_str(tree.xpath('//meta[@property="og:title"]/@content'))
            or self._first_str(
                tree.xpath('//div[contains(@class,"det-info")]//h1/text()')
            )
        )

        author = self._first_str(
            tree.xpath('//meta[@property="og:novel:author"]/@content')
        ) or self._first_str(
            tree.xpath(
                '//div[contains(@class,"det-info")]//p[contains(@class,"_tags")]//strong[1]//a/text()'
            )
        )

        category = self._first_str(
            tree.xpath('//meta[@property="og:novel:category"]/@content')
        ) or self._first_str(
            tree.xpath(
                '//div[contains(@class,"det-info")]//p[contains(@class,"_tags")]//strong[2]//span/text()'
            )
        )

        serial_status = self._first_str(
            tree.xpath('//meta[@property="og:novel:status"]/@content')
        ) or self._first_str(
            tree.xpath(
                '//div[contains(@class,"det-info")]//p[contains(@class,"_tags")]//strong[3]//span/text()'
            )
        )

        word_count = self._first_str(
            tree.xpath(
                '//div[contains(@class,"det-info")]//p[contains(@class,"_tags")]//strong//span[contains(text(),"字")]/text()'
            )
        )

        update_time = self._first_str(
            tree.xpath('//meta[@property="og:novel:update_time"]/@content')
        ) or self._first_str(tree.xpath('//div[@id="Contents"]//p/small/text()'))

        cover_url = self._first_str(
            tree.xpath('//meta[@property="og:image"]/@content')
        ) or self._first_str(
            tree.xpath(
                '//div[contains(@class,"det-info")]//div[contains(@class,"cover")]//img/@src'
            )
        )

        summary = self._first_str(
            tree.xpath('//meta[@property="og:description"]/@content'),
            replaces=[("\r", ""), ("\n\n", "\n")],
        )
        if not summary:
            summary = self._join_strs(
                tree.xpath(
                    '//div[contains(@class,"det-info")]//div[contains(@class,"det-abt")]//p//text()'
                ),
                replaces=[("\r", ""), ("\n\n", "\n")],
            )

        # --- Chapter volumes ---
        volumes: list[VolumeInfoDict] = []
        current_volume_name: str | None = None
        current_chapters: list[ChapterInfoDict] = []

        def flush_volume() -> None:
            nonlocal current_volume_name, current_chapters
            if not current_chapters:
                return
            volumes.append(
                {
                    "volume_name": current_volume_name or "正文",
                    "chapters": current_chapters,
                }
            )
            current_volume_name, current_chapters = None, []

        # Iterate ordered <li> under #chapterList
        for li in tree.xpath('//ol[@id="chapterList"]/li'):
            li_class = li.get("class") or ""
            # Volume marker
            if "volumes" in li_class:
                flush_volume()
                current_volume_name = self._first_str(li.xpath(".//text()"))
                continue

            # Chapter item
            a = li.xpath(".//a")
            if not a:
                continue
            href = (a[0].get("href") or "").strip()
            if not href:
                continue
            title = self._first_str(a[0].xpath(".//text()"))
            chapter_id = (
                "" if "javascript" in href else href.rsplit("/", 1)[-1].split(".", 1)[0]
            )
            current_chapters.append(
                {"title": title, "url": href, "chapterId": chapter_id}
            )

        flush_volume()

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "serial_status": serial_status,
            "word_count": word_count,
            "update_time": update_time,
            "summary": summary,
            "tags": [category] if category else [],
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

        title: str = ""
        paragraphs: list[str] = []

        for curr_html in html_list:
            tree = html.fromstring(curr_html)
            decrypt: bool = "/en/common/read.ttf" in curr_html

            if not title:
                title = self._first_str(
                    tree.xpath('//div[@id="mlfy_main_text"]/h1/text()')
                )

            for node in tree.xpath(
                '//div[@id="TextContent"]//p | //div[@id="TextContent"]//img'
            ):
                tag = node.tag.lower()
                if tag == "p":
                    txt = "".join(node.xpath(".//text()")).strip()
                    if decrypt:
                        txt = self._apply_font_mapping(txt)
                    if txt:
                        paragraphs.append(txt)
                elif tag == "img":
                    src = (node.get("src") or "").strip()
                    if src:
                        paragraphs.append(f'<img src="{src}" />')

        content = "\n".join(paragraphs)
        if not content.strip():
            return None

        m = self._NEXTPAGE_RE.search(html_list[-1])
        next_cid = m.group(1) if m else None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {
                "site": self.site_name,
                "next_cid": next_cid,
            },
        }

    @classmethod
    def _apply_font_mapping(cls, text: str) -> str:
        """
        Apply font mapping to the input text.
        """
        if not cls._FONT_MAP:
            cls._FONT_MAP = json.loads(YODU_MAP_PATH.read_text(encoding="utf-8"))
        return "".join(cls._FONT_MAP.get(ch, ch) for ch in text)
