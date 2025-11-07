#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.wxsck.parser
-------------------------------------------
"""

from typing import Any

from lxml import html
from novel_downloader.plugins.base.parser import BaseParser
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import (
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    VolumeInfoDict,
)


@registrar.register_parser()
class WxsckParser(BaseParser):
    """
    Parser for 万相书城 book pages.
    """

    site_name: str = "wxsck"
    BASE_URL = "https://wxsck.com"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        book_name = self._first_str(
            tree.xpath('//meta[@property="og:novel:book_name"]/@content')
        )
        author = self._first_str(
            tree.xpath('//meta[@property="og:novel:author"]/@content')
        )
        serial_status = self._first_str(
            tree.xpath('//meta[@property="og:novel:status"]/@content')
        )
        update_time = self._first_str(
            tree.xpath('//meta[@property="og:novel:update_time"]/@content')
        )
        cover_url = self._first_str(tree.xpath('//meta[@property="og:image"]/@content'))
        if cover_url and not cover_url.startswith("http"):
            cover_url = self.BASE_URL + cover_url

        book_type = self._first_str(
            tree.xpath('//meta[@property="og:novel:category"]/@content')
        )
        tags = [book_type] if book_type else []

        summary = self._join_strs(tree.xpath('//div[@class="book-detail"]/text()'))
        if not summary:
            summary = self._first_str(
                tree.xpath('//meta[@property="og:description"]/@content')
            )

        chapters: list[ChapterInfoDict] = [
            {
                "title": (a.text or "").strip(),
                "url": (a.get("href") or "").strip(),
                "chapterId": (a.get("href") or "").rsplit("/", 1)[-1].split(".", 1)[0],
            }
            for a in tree.xpath('//div[@id="all-chapter"]//a')
        ]

        if not chapters:
            return None

        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "serial_status": serial_status,
            "summary": summary,
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
            return None

        title = ""
        paragraphs: list[str] = []
        for curr_html in html_list:
            tree = html.fromstring(curr_html)
            if not title:
                title = self._first_str(tree.xpath('//h1[@class="cont-title"]/text()'))

            lines = [
                text
                for p in tree.xpath('//div[@id="cont-body"]//p')
                if (text := p.text_content().strip())
            ]
            page_text = "\n".join(lines)
            if page_text:
                paragraphs.append(page_text)

        if not paragraphs:
            return None

        content = "\n".join(paragraphs)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
