#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.quanben5.parser
----------------------------------------------

"""

from datetime import datetime
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
class Quanben5Parser(BaseParser):
    """
    Parser for 全本小说网 book pages.
    """

    site_name: str = "quanben5"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])
        book_name = self._first_str(tree.xpath("//h3/span/text()"))
        author = self._first_str(
            tree.xpath(
                '//p[@class="info"][contains(., "作者")]/span[@class="author"]/text()'
            )
        )
        cover_url = self._first_str(tree.xpath('//div[@class="pic"]/img/@src'))
        category = self._first_str(
            tree.xpath('//p[@class="info"][contains(., "类别")]/span/text()')
        )
        tags = [category] if category else []
        update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        summary = self._first_str(tree.xpath('//p[@class="description"]/text()'))

        chapters: list[ChapterInfoDict] = []
        for li in tree.xpath('//ul[@class="list"]/li'):
            link = li.xpath(".//a")[0]
            href = link.get("href", "").strip()
            title = self._first_str(link.xpath(".//span/text()"))
            # '/n/toutian/83840.html' -> '83840'
            chapter_id = href.rstrip(".html").split("/")[-1]
            chapters.append({"title": title, "url": href, "chapterId": chapter_id})

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

        # Extract the chapter title
        title = self._first_str(tree.xpath('//h1[@class="title1"]/text()'))

        # Extract all <p> text within the content container
        paragraphs = tree.xpath('//div[@id="content"]/p/text()')
        # Clean whitespace and join with double newlines
        content = "\n".join(p.strip() for p in paragraphs if p.strip())

        if not content:
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
