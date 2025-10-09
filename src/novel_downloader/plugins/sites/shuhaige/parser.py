#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.shuhaige.parser
----------------------------------------------

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
class ShuhaigeParser(BaseParser):
    """
    Parser for 书海阁小说网 book pages.
    """

    site_name: str = "shuhaige"
    ADS = {
        r"www\.shuhaige\.net",
        "书海阁小说网",
        "点击下一页",
    }

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

        cover_url = self._first_str(tree.xpath('//div[@id="fmimg"]/img/@src'))

        update_time = self._first_str(
            tree.xpath('//div[@id="info"]/p[3]/text()'),
            replaces=[("最后更新：", "")],
        )

        summary = self._first_str(tree.xpath('//div[@id="intro"]/p[1]/text()'))

        book_type = self._first_str(tree.xpath('//div[@class="con_top"]/a[2]/text()'))
        tags = [book_type] if book_type else []

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
            "tags": tags,
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

        title = ""
        paragraphs: list[str] = []
        for curr_html in html_list:
            tree = html.fromstring(curr_html)
            if not title:
                title = self._first_str(
                    tree.xpath('//div[@class="bookname"]/h1/text()')
                )

            lines = [
                text
                for p in tree.xpath('//div[@id="content"]//p')
                if (text := "".join(p.itertext()).strip())
                and not self._is_ad_line(text)
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
