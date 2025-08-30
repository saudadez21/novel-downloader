#!/usr/bin/env python3
"""
novel_downloader.core.parsers.linovelib
---------------------------------------

"""

import json
from itertools import islice
from typing import Any

from lxml import html

from novel_downloader.core.parsers.base import BaseParser
from novel_downloader.core.parsers.registry import register_parser
from novel_downloader.models import (
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    VolumeInfoDict,
)
from novel_downloader.utils.constants import LINOVELIB_FONT_MAP_PATH


@register_parser(
    site_keys=["linovelib"],
)
class LinovelibParser(BaseParser):
    """
    Parser for 哔哩轻小说 book pages.
    """

    # Book info XPaths
    _BOOK_NAME_XPATH = '//div[@class="book-info"]/h1[@class="book-name"]/text()'
    _AUTHOR_XPATH = '//div[@class="au-name"]/a[1]/text()'
    _COVER_URL_XPATH = '//div[contains(@class, "book-img")]//img/@src'
    _UPDATE_TIME_XPATH = (
        '//div[@class="nums"]/span[contains(text(), "最后更新")]/text()'  # noqa: E501
    )
    _SERIAL_STATUS_XPATH = '//div[@class="book-label"]/a[@class="state"]/text()'
    _WORD_COUNT_XPATH = '//div[@class="nums"]/span[contains(text(), "字数")]/text()'
    _SUMMARY_XPATH = '//div[contains(@class, "book-dec")]/p//text()'

    _CHAPTERS_XPATH = '//div[@class="book-new-chapter"]/div[contains(@class, "tit")]/a'

    # Chapter XPaths
    _CHAPTER_TITLE_XPATH = "//div[@id='mlfy_main_text']/h1/text()"
    _CHAPTER_CONTENT_NODES_XPATH = "//div[@id='TextContent']/*[self::p or self::img]"

    _FONT_MAP: dict[str, str] = json.loads(
        LINOVELIB_FONT_MAP_PATH.read_text(encoding="utf-8")
    )  # 注意 json 前 3500 条的内容不必要不修改
    _BLANK_SET: set[str] = set(islice(_FONT_MAP.values(), 3500))

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None
        tree = html.fromstring(html_list[0])

        book_name = self._first_str(tree.xpath(self._BOOK_NAME_XPATH))
        author = self._first_str(tree.xpath(self._AUTHOR_XPATH))
        cover_url = self._first_str(tree.xpath(self._COVER_URL_XPATH))
        update_time = self._first_str(
            tree.xpath(self._UPDATE_TIME_XPATH), replaces=[("最后更新：", "")]
        )
        serial_status = self._first_str(tree.xpath(self._SERIAL_STATUS_XPATH))
        word_count = self._first_str(
            tree.xpath(self._WORD_COUNT_XPATH), replaces=[("最后更新：", "")]
        )

        summary = self._extract_intro(tree, self._SUMMARY_XPATH)

        vol_pages = html_list[1:]
        volumes: list[VolumeInfoDict] = []
        for vol_page in vol_pages:
            vol_tree = html.fromstring(vol_page)
            volume_cover = self._first_str(vol_tree.xpath(self._COVER_URL_XPATH))
            volume_name = self._first_str(vol_tree.xpath(self._BOOK_NAME_XPATH))
            vol_update_time = self._first_str(
                vol_tree.xpath(self._UPDATE_TIME_XPATH), replaces=[("最后更新：", "")]
            )
            vol_word_count = self._first_str(
                vol_tree.xpath(self._WORD_COUNT_XPATH), replaces=[("字数：", "")]
            )
            volume_intro = self._extract_intro(vol_tree, self._SUMMARY_XPATH)

            chapters: list[ChapterInfoDict] = []
            chapter_elements = vol_tree.xpath(self._CHAPTERS_XPATH)
            for a in chapter_elements:
                title = a.text.strip()
                url = a.attrib.get("href", "").strip()
                # '/novel/4668/276082.html' -> '276082'
                cid = url.split("/")[-1].split(".")[0]
                chapters.append({"title": title, "url": url, "chapterId": cid})

            volumes.append(
                {
                    "volume_name": volume_name,
                    "volume_cover": volume_cover,
                    "update_time": vol_update_time,
                    "word_count": vol_word_count,
                    "volume_intro": volume_intro,
                    "chapters": chapters,
                }
            )

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "serial_status": serial_status,
            "word_count": word_count,
            "summary": summary,
            "update_time": update_time,
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
        title_text: str = ""
        contents: list[str] = []
        for curr_html in html_list:
            is_encrypted = self._is_encrypted(curr_html)
            tree = html.fromstring(curr_html)

            if not title_text:
                titles = tree.xpath(self._CHAPTER_TITLE_XPATH)
                if titles:
                    title_text = titles[0].strip()

            content_container = tree.xpath("//div[@id='TextContent']")
            if not content_container:
                continue
            container = content_container[0]
            nodes = container.xpath("./p | ./img")
            all_p = container.xpath("./p")
            total_p = len(all_p)
            p_counter = 0

            for node in nodes:
                tag = node.tag.lower()
                if tag == "p":
                    raw_text = "".join(node.xpath(".//text()")).strip()
                    if not raw_text:
                        continue

                    if is_encrypted and p_counter == total_p - 2:
                        raw_text = self._apply_font_map(raw_text)

                    contents.append(raw_text)
                    p_counter += 1

                elif tag == "img":
                    src = node.get("data-src") or node.get("src", "")
                    src = src.strip()
                    if src:
                        contents.append(f'<img src="{src}" />')
        return {
            "id": chapter_id,
            "title": title_text,
            "content": "\n".join(contents),
            "extra": {"site": "linovelib"},
        }

    @staticmethod
    def _extract_intro(tree: html.HtmlElement, xpath: str) -> str:
        paragraphs = tree.xpath(xpath.replace("//text()", ""))
        lines = []
        for p in paragraphs:
            text_segments = p.xpath(".//text()")
            cleaned = [seg.strip() for seg in text_segments if seg.strip()]
            lines.append("\n".join(cleaned))
        return "\n".join(lines)

    @staticmethod
    def _is_encrypted(html: str) -> bool:
        """
        Determine whether HTML content likely uses encrypted or obfuscated fonts.
        """
        return "CSSStyleSheet" in html

    @classmethod
    def _apply_font_map(cls, text: str) -> str:
        """
        Apply font mapping to the input text,
        skipping characters in blank set.
        """
        return "".join(cls._FONT_MAP.get(c, c) for c in text if c not in cls._BLANK_SET)
