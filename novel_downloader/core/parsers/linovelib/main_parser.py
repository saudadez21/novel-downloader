#!/usr/bin/env python3
"""
novel_downloader.core.parsers.linovelib.main_parser
---------------------------------------------------

"""

import json
from itertools import islice
from pathlib import PurePosixPath
from typing import Any

from lxml import html

from novel_downloader.core.parsers.base import BaseParser
from novel_downloader.models import ChapterDict
from novel_downloader.utils.constants import LINOVELIB_FONT_MAP_PATH


class LinovelibParser(BaseParser):
    """ """

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
    ) -> dict[str, Any]:
        """
        Parse a book info page and extract metadata and chapter structure.

        :param html_list: Raw HTML of the book info page.
        :return: Parsed metadata and chapter structure as a dictionary.
        """
        if not html_list:
            return {}
        info_tree = html.fromstring(html_list[0])
        result: dict[str, Any] = {}

        result["book_name"] = self._safe_xpath(info_tree, self._BOOK_NAME_XPATH)
        result["author"] = self._safe_xpath(info_tree, self._AUTHOR_XPATH)
        result["cover_url"] = self._safe_xpath(info_tree, self._COVER_URL_XPATH)
        result["update_time"] = self._safe_xpath(
            info_tree, self._UPDATE_TIME_XPATH, replace=("最后更新：", "")
        )
        result["serial_status"] = self._safe_xpath(info_tree, self._SERIAL_STATUS_XPATH)
        result["word_count"] = self._safe_xpath(
            info_tree, self._WORD_COUNT_XPATH, replace=("字数：", "")
        )

        result["summary"] = self._extract_intro(info_tree, self._SUMMARY_XPATH)

        vol_pages = html_list[1:]
        volumes: list[dict[str, Any]] = []
        for vol_page in vol_pages:
            vol_tree = html.fromstring(vol_page)
            volume_cover = self._safe_xpath(vol_tree, self._COVER_URL_XPATH)
            volume_name = self._safe_xpath(vol_tree, self._BOOK_NAME_XPATH)
            update_time = self._safe_xpath(
                vol_tree, self._UPDATE_TIME_XPATH, replace=("最后更新：", "")
            )
            word_count = self._safe_xpath(
                vol_tree, self._WORD_COUNT_XPATH, replace=("字数：", "")
            )
            volume_intro = self._extract_intro(vol_tree, self._SUMMARY_XPATH)

            chapters = []
            chapter_elements = vol_tree.xpath(self._CHAPTERS_XPATH)
            for a in chapter_elements:
                title = a.text.strip()
                url = a.attrib.get("href", "").strip()
                chap_path = PurePosixPath(url.rstrip("/"))
                chapters.append(
                    {"title": title, "url": url, "chapterId": chap_path.stem}
                )

            volumes.append(
                {
                    "volume_name": volume_name,
                    "volume_cover": volume_cover,
                    "update_time": update_time,
                    "word_count": word_count,
                    "volume_intro": volume_intro,
                    "chapters": chapters,
                }
            )
        result["volumes"] = volumes

        return result

    def parse_chapter(
        self,
        html_list: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        """
        Parse chapter pages and extract clean text or simplified HTML.

        :param html_list: Raw HTML of the chapter page.
        :param chapter_id: Identifier of the chapter being parsed.
        :return: Cleaned chapter content as plain text or minimal HTML.
        """
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
            "content": "\n\n".join(contents),
            "extra": {"site": "linovelib"},
        }

    def _safe_xpath(
        self,
        tree: html.HtmlElement,
        path: str,
        replace: tuple[str, str] | None = None,
    ) -> str:
        result = tree.xpath(path)
        if not result:
            return ""
        value: str = result[0].strip()
        if replace:
            old, new = replace
            value = value.replace(old, new)
        return value

    @staticmethod
    def _extract_intro(tree: html.HtmlElement, xpath: str) -> str:
        paragraphs = tree.xpath(xpath.replace("//text()", ""))
        lines = []
        for p in paragraphs:
            text_segments = p.xpath(".//text()")
            cleaned = [seg.strip() for seg in text_segments if seg.strip()]
            lines.append("\n".join(cleaned))
        return "\n\n".join(lines)

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
