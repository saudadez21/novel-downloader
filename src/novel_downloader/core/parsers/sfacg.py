#!/usr/bin/env python3
"""
novel_downloader.core.parsers.sfacg
-----------------------------------

"""

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


@register_parser(
    site_keys=["sfacg"],
)
class SfacgParser(BaseParser):
    """
    Parser for sfacg book pages.
    """

    # Book info XPaths
    _BOOK_NAME_XPATH = '//ul[@class="book_info"]//span[@class="book_newtitle"]/text()'
    _AUTHOR_INFO_XPATH = '//ul[@class="book_info"]//span[@class="book_info3"]/text()'
    _UPDATE_TIME_XPATH = '//ul[@class="book_info"]//span[@class="book_info3"]/br/following-sibling::text()'  # noqa: E501
    _COVER_URL_XPATH = '//ul[@class="book_info"]//li/img/@src'
    # _STATUS_XPATH = '//ul[@class="book_info"]//div[@class="book_info2"]/span/text()'
    _STATUS_XPATH = (
        '//ul[@class="book_info"]//div[@class="book_info2"]/span/text()'
        ' and (contains(., "完结") or contains(., "连载"))]/text()'
    )
    _SUMMARY_XPATH = '//ul[@class="book_profile"]/li[@class="book_bk_qs1"]/text()'

    # Catalog XPaths
    _VOLUME_TITLE_XPATH = '//div[@class="mulu"]/text()'
    _VOLUME_CONTENT_XPATH = '//div[@class="Content_Frame"]'
    _CHAPTER_LIST_XPATH = './/ul[@class="mulu_list"]/a'

    # Chapter XPaths
    _CHAPTER_TEXT_XPATH = (
        '//div[@class="yuedu Content_Frame"]//div[@style="text-indent: 2em;"]/text()'
    )
    _CHAPTER_CONTENT_NODES_XPATH = (
        '//div[@class="yuedu Content_Frame"]//div[@style="text-indent: 2em;"]/*'
    )
    _CHAPTER_TITLE_XPATH = '//ul[@class="menu_top_list book_view_top"]/li[2]/text()'

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if len(html_list) < 2:
            return None

        info_tree = html.fromstring(html_list[0])
        catalog_tree = html.fromstring(html_list[1])

        # Book metadata
        book_name = self._first_str(info_tree.xpath(self._BOOK_NAME_XPATH))

        book_info3_str = self._first_str(info_tree.xpath(self._AUTHOR_INFO_XPATH))
        author, _, word_count = (p.strip() for p in book_info3_str.partition("/"))

        update_time = self._first_str(info_tree.xpath(self._UPDATE_TIME_XPATH))

        cover_url = "https:" + self._first_str(info_tree.xpath(self._COVER_URL_XPATH))

        serial_status = self._first_str(info_tree.xpath(self._STATUS_XPATH))

        summary_elem = info_tree.xpath(self._SUMMARY_XPATH)
        summary = "".join(summary_elem).strip()

        # Chapter structure
        volume_titles = catalog_tree.xpath(self._VOLUME_TITLE_XPATH)
        volume_blocks = catalog_tree.xpath(self._VOLUME_CONTENT_XPATH)

        volumes: list[VolumeInfoDict] = []
        for vol_title, vol_block in zip(volume_titles, volume_blocks, strict=False):
            chapters: list[ChapterInfoDict] = []
            for a in vol_block.xpath(self._CHAPTER_LIST_XPATH):
                href = a.xpath("./@href")[0] if a.xpath("./@href") else ""
                title = "".join(a.xpath(".//li//text()")).strip()
                chapter_id = href.split("/")[-2] if href else ""
                chapters.append(
                    {
                        "title": title,
                        "url": href,
                        "chapterId": chapter_id,
                    }
                )
            volumes.append(
                {
                    "volume_name": vol_title.strip(),
                    "chapters": chapters,
                }
            )

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "word_count": word_count,
            "serial_status": serial_status,
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
        keywords = [
            "本章为VIP章节",  # 本章为VIP章节，订阅后可立即阅读
        ]
        if any(kw in html_list[0] for kw in keywords):
            return None
        tree = html.fromstring(html_list[0])

        content_lines: list[str] = []
        content_nodes = tree.xpath(self._CHAPTER_CONTENT_NODES_XPATH)
        for node in content_nodes:
            tag = node.tag.lower()
            if tag == "p":
                text = "".join(node.xpath(".//text()")).strip()
                if text:
                    content_lines.append(text)
            elif tag == "img":
                src = node.get("src", "").strip()
                if src:
                    # embed image as HTML tag
                    content_lines.append(f'<img src="{src}" />')

        if not content_lines:
            raw_text_parts = tree.xpath(self._CHAPTER_TEXT_XPATH)
            content_lines = [txt.strip() for txt in raw_text_parts if txt.strip()]

        content = "\n".join(content_lines).strip()
        if not content:
            return None

        title_part = tree.xpath(self._CHAPTER_TITLE_XPATH)
        title = title_part[0].strip() if title_part else ""

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": "sfacg"},
        }
