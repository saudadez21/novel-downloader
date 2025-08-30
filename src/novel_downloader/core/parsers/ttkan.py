#!/usr/bin/env python3
"""
novel_downloader.core.parsers.ttkan
-----------------------------------

"""

from datetime import datetime
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
    site_keys=["ttkan"],
)
class TtkanParser(BaseParser):
    """
    Parser for 天天看小說 book pages.
    """

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        # Book metadata
        book_name = self._first_str(
            tree.xpath('//div[contains(@class,"novel_info")]//h1/text()')
        )

        author = self._first_str(
            tree.xpath(
                '//div[contains(@class,"novel_info")]//li[span/text()="作者："]/a/text()'
            )
        )

        cover_url = self._first_str(
            tree.xpath('//div[contains(@class,"novel_info")]//amp-img/@src')
        )

        serial_status = self._first_str(
            tree.xpath(
                '//div[contains(@class,"novel_info")]//span[contains(@class,"state_serial")]/text()'
            )
        )

        update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Summary
        summary_nodes = tree.xpath('//div[@class="description"]//p/text()')
        summary = "".join(summary_nodes).strip()

        # Single "正文" volume with all chapter links
        chapters: list[ChapterInfoDict] = []
        for a in tree.xpath('//div[@class="full_chapters"]/div[1]/a'):
            url = a.get("href", "").strip()
            title = a.text_content().strip()
            # '/novel/pagea/wushenzhuzai-anmoshi_6094.html' -> '6094'
            chap_id = url.rstrip(".html").split("_")[-1]
            chapters.append(
                {
                    "chapterId": chap_id,
                    "title": title,
                    "url": url,
                }
            )

        volumes: list[VolumeInfoDict] = [
            {
                "volume_name": "正文",
                "chapters": chapters,
            }
        ]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
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

        content = "\n".join(lines).strip()
        if not content:
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": "ttkan"},
        }
