#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.biquge345.parser
-----------------------------------------------
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
class Biquge345Parser(BaseParser):
    """
    Parser for 笔趣阁 book pages.
    """

    site_name: str = "biquge345"
    BASE_URL = "https://www.biquge345.com"

    ADS = {
        "biquge345",
        "笔趣阁小说网",
    }

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        book_name = self._first_str(
            tree.xpath('//div[@class="right_border"]/h1/text()')
        )
        author = self._first_str(
            tree.xpath('//div[@class="xinxi"]/span[@class="x1"][1]/a/text()')
        )

        cover_url = self._first_str(tree.xpath('//div[@class="zhutu"]/img/@src'))
        if cover_url.startswith("//"):
            cover_url = "https:" + cover_url
        elif cover_url.startswith("/"):
            cover_url = self.BASE_URL + cover_url

        update_time = self._first_str(
            tree.xpath('//div[@class="xinxi"]/span[@class="x2"][1]/text()'),
            replaces=[("更新时间：", "")],
        )

        genre = self._first_str(
            tree.xpath('//div[@class="xinxi"]/span[@class="x1"][2]/text()'),
            replaces=[("类型：", "")],
        )
        tags = [genre] if genre else []

        summary = self._join_strs(
            tree.xpath('//div[@class="xinxi"]/div[@class="x3"]/text()')
        )

        # Chapters from the book_list
        chapters: list[ChapterInfoDict] = []
        for a in tree.xpath('//div[@class="border"]//ul[@class="info"]//a'):
            url = a.get("href", "").strip()
            chapter_id = url.rsplit("/", 1)[-1].split(".", 1)[0]
            title = a.text_content().strip()
            chapters.append(
                {
                    "title": title,
                    "url": url,
                    "chapterId": chapter_id,
                }
            )

        if not chapters:
            return None

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

        tree = html.fromstring(html_list[0])

        title = self._first_str(tree.xpath('//div[@id="neirong"]//h1/text()'))

        paragraphs = []
        for txt in tree.xpath('//div[@id="txt"]//text()'):
            line = txt.strip()
            # Skip empty/instruction/ad lines
            if not line or self._is_ad_line(txt):
                continue
            paragraphs.append(line)

        if not paragraphs:
            return None

        content = "\n".join(paragraphs)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
