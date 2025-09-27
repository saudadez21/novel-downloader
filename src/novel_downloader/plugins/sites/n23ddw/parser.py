#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n23ddw.parser
--------------------------------------------

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
class N23ddwParser(BaseParser):
    """
    Parser for 顶点小说网 book pages.
    """

    site_name: str = "n23ddw"

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
        cover_url = self._first_str(tree.xpath('//meta[@property="og:image"]/@content'))
        update_time = self._first_str(
            tree.xpath('//meta[@property="og:novel:update_time"]/@content')
        )
        serial_status = self._first_str(
            tree.xpath('//meta[@property="og:novel:status"]/@content')
        )
        summary = self._first_str(
            tree.xpath('//meta[@property="og:description"]/@content')
        )
        category = self._first_str(
            tree.xpath('//meta[@property="og:novel:category"]/@content')
        )
        tags = [category] if category else []

        chapters: list[ChapterInfoDict] = [
            {
                "title": self._first_str(a.xpath(".//dd/text() | text()")),
                "url": (a.get("href") or "").strip(),
                "chapterId": (a.get("href") or "").rsplit("/", 1)[-1].split(".", 1)[0],
            }
            for a in tree.xpath('//div[@id="list"]/dl/dt[2]/following-sibling::a')
        ]
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
                title = self._first_str(
                    tree.xpath('//h1[contains(@class,"bookname")]/text()')
                )
                title = title.rsplit("（1/", 1)[0]

            for p in tree.xpath('//div[@id="content"]//div[@id="booktxt"]/p'):
                text = self._join_strs(p.xpath(".//text()"))
                if text:
                    paragraphs.append(text)

        content = "\n".join(paragraphs)
        if not content.strip():
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
