#!/usr/bin/env python3
"""
novel_downloader.core.parsers.sfacg.main_parser
-----------------------------------------------

"""

from typing import Any

from lxml import html

from novel_downloader.core.parsers.base import BaseParser
from novel_downloader.models import ChapterDict


class SfacgParser(BaseParser):
    """ """

    # Book info XPaths
    _BOOK_NAME_XPATH = '//ul[@class="book_info"]//span[@class="book_newtitle"]/text()'
    _AUTHOR_INFO_XPATH = '//ul[@class="book_info"]//span[@class="book_info3"]/text()'
    _UPDATE_TIME_XPATH = '//ul[@class="book_info"]//span[@class="book_info3"]/br/following-sibling::text()'  # noqa: E501
    _COVER_URL_XPATH = '//ul[@class="book_info"]//li/img/@src'
    _STATUS_XPATH = '//ul[@class="book_info"]//div[@class="book_info2"]/span/text()'
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
    ) -> dict[str, Any]:
        """
        Parse a book info page and extract metadata and chapter structure.

        :param html_list: Raw HTML of the book info page.
        :return: Parsed metadata and chapter structure as a dictionary.
        """
        if len(html_list) < 2:
            return {}

        info_tree = html.fromstring(html_list[0])
        catalog_tree = html.fromstring(html_list[1])

        result: dict[str, Any] = {}

        # Book metadata
        book_name = info_tree.xpath(self._BOOK_NAME_XPATH)
        result["book_name"] = book_name[0].strip() if book_name else ""

        book_info3 = info_tree.xpath(self._AUTHOR_INFO_XPATH)
        result["author"] = book_info3[0].split("/")[0].strip() if book_info3 else ""
        result["word_count"] = (
            book_info3[0].split("/")[1].strip()
            if book_info3 and len(book_info3[0].split("/")) > 1
            else ""
        )

        book_info3_br = info_tree.xpath(self._UPDATE_TIME_XPATH)
        result["update_time"] = book_info3_br[0].strip() if book_info3_br else ""

        cover_url = info_tree.xpath(self._COVER_URL_XPATH)
        result["cover_url"] = "https:" + cover_url[0] if cover_url else ""

        serial_status = info_tree.xpath(self._STATUS_XPATH)
        result["serial_status"] = next(
            (s for s in serial_status if "完结" in s or "连载" in s), ""
        )

        summary = info_tree.xpath(self._SUMMARY_XPATH)
        result["summary"] = "".join(summary).strip()

        # Chapter structure
        volume_titles = catalog_tree.xpath(self._VOLUME_TITLE_XPATH)
        volume_blocks = catalog_tree.xpath(self._VOLUME_CONTENT_XPATH)

        volumes = []
        for vol_title, vol_block in zip(volume_titles, volume_blocks, strict=False):
            chapters = []
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
        result["volumes"] = volumes

        return result

    def parse_chapter(
        self,
        html_list: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        """
        Parse a single chapter page and extract clean text or simplified HTML.

        :param html_list: Raw HTML of the chapter page.
        :param chapter_id: Identifier of the chapter being parsed.
        :return: Cleaned chapter content as plain text or minimal HTML.
        """
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

        content = "\n\n".join(content_lines).strip()
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
