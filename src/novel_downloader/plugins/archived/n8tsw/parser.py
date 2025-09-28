#!/usr/bin/env python3
"""
novel_downloader.plugins.archived.n8tsw.parser
----------------------------------------------

"""

from typing import Any

from lxml import html
from novel_downloader.plugins.base.parser import BaseParser
from novel_downloader.schemas import (
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    VolumeInfoDict,
)


class N8tswParser(BaseParser):
    """
    Parser for 笔趣阁 book pages.
    """

    site_name: str = "n8tsw"
    BASE_URL = "https://www.8tsw.com"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        book_name = self._first_str(tree.xpath('//div[@id="info"]/h1/text()'))
        author = self._first_str(tree.xpath('//div[@id="info"]/p[1]/a/text()'))
        author = self._first_str(
            tree.xpath('//div[@id="info"]/p[1]/text()'),
            replaces=[("\xa0", ""), ("作者：", "")],
        )

        cover_url = self.BASE_URL + self._first_str(
            tree.xpath('//div[@id="fmimg"]/img/@src')
        )

        update_time = self._first_str(
            tree.xpath('//div[@id="info"]/p[3]/text()'),
            replaces=[("最后更新：", "")],
        )

        summary = self._join_strs(tree.xpath('//div[@id="intro"]/p[1]/text()'))

        chapters: list[ChapterInfoDict] = [
            {
                "title": (a.text or "").strip(),
                "url": (a.get("href") or "").strip(),
                "chapterId": (a.get("href") or "").rsplit("/", 1)[-1].split(".", 1)[0],
            }
            for a in tree.xpath(
                '//div[@id="list"]/dl/dt[contains(., "正文")]/following-sibling::dd/a'
            )
        ]

        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
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

        title = self._first_str(tree.xpath('//div[@class="bookname"]/h1/text()'))

        paragraphs: list[str] = [
            s.strip().replace("\u3000", "").replace("\xa0", "")
            for s in tree.xpath('//div[@id="content"]//text()')
            if s and s.strip()
        ]

        content = "\n".join(paragraphs)
        if not content.strip():
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
