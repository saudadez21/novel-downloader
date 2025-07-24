#!/usr/bin/env python3
"""
novel_downloader.core.parsers.ttkan
-----------------------------------

"""

import re
from datetime import datetime
from typing import Any

from lxml import html

from novel_downloader.core.parsers.base import BaseParser
from novel_downloader.core.parsers.registry import register_parser
from novel_downloader.models import ChapterDict


@register_parser(
    site_keys=["ttkan"],
)
class TtkanParser(BaseParser):
    """ """

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

        tree = html.fromstring(html_list[0])

        result: dict[str, Any] = {}

        # Book metadata
        result["book_name"] = tree.xpath(
            '//div[contains(@class,"novel_info")]//h1/text()'
        )[0].strip()

        result["author"] = tree.xpath(
            '//div[contains(@class,"novel_info")]//li[span/text()="作者："]/a/text()'
        )[0].strip()

        cover = tree.xpath('//div[contains(@class,"novel_info")]//amp-img/@src')
        result["cover_url"] = cover[0] if cover else ""

        status = tree.xpath(
            '//div[contains(@class,"novel_info")]//span[contains(@class,"state_serial")]/text()'
        )
        result["serial_status"] = status[0].strip() if status else ""

        result["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Summary
        summary_nodes = tree.xpath('//div[@class="description"]//p/text()')
        result["summary"] = "".join(summary_nodes).strip()

        # Single "正文" volume with all chapter links
        chapters = []
        for a in tree.xpath('//div[@class="full_chapters"]/div[1]/a'):
            url = a.get("href", "").strip()
            title = a.text_content().strip()
            m = re.search(r"_(\d+)\.html", url)
            chap_id = m.group(1) if m else ""
            chapters.append(
                {
                    "chapterId": chap_id,
                    "title": title,
                    "url": url,
                }
            )

        result["volumes"] = [
            {
                "volume_name": "正文",
                "chapters": chapters,
            }
        ]

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
        tree = html.fromstring(html_list[0])

        # Title
        title_nodes = tree.xpath('//div[@class="title"]/h1/text()')
        title = title_nodes[0].strip() if title_nodes else ""

        # Content paragraphs under <div class="content">
        paras = tree.xpath('//div[@class="content"]/p')
        lines = []
        for p in paras:
            text = p.text_content().strip()
            if text:
                lines.append(text)

        content = "\n\n".join(lines).strip()
        if not content:
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": "ttkan"},
        }
