#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.haiwaishubao.parser
--------------------------------------------------
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
class HaiwaishubaoParser(BaseParser):
    """
    Parser for 海外书包 book pages.
    """

    site_name: str = "haiwaishubao"

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
            tree.xpath('//meta[@property="og:title"]/@content')
            or tree.xpath('//p[@class="title"]/text()')
        )
        author = self._first_str(
            tree.xpath('//meta[@property="og:novel:author"]/@content')
            or tree.xpath('//p[@class="author"]//a/text()')
        )
        cover_url = self._first_str(
            tree.xpath('//meta[@property="og:image"]/@content')
            or tree.xpath('//div[@class="BGsectionOne-top-left"]/img/@src')
        )
        update_time = self._first_str(
            tree.xpath('//meta[@property="og:novel:update_time"]/@content')
            or tree.xpath('//p[@class="time"]/span/text()')
        )
        serial_status = self._first_str(
            tree.xpath('//meta[@property="og:novel:status"]/@content')
            or tree.xpath('//p[contains(@class,"status")]/span/text()')
        )
        category = self._first_str(
            tree.xpath('//meta[@property="og:novel:category"]/@content')
            or tree.xpath('//p[@class="category"]//a/text()')
        )
        summary = self._join_strs(
            tree.xpath('//meta[@property="og:description"]/@content'),
            replaces=[("&emsp;", "")],
        )
        tags = [category] if category else []

        # Chapter volumes & listings
        chapters: list[ChapterInfoDict] = []
        for catalog_html in html_list[1:]:
            cat_tree = html.fromstring(catalog_html)
            for a in cat_tree.xpath('//ol[contains(@class,"BCsectionTwo-top")]//a'):
                href = (a.get("href") or "").strip()
                if not href:
                    continue
                title = self._first_str(a.xpath(".//text()"))
                chapter_id = href.rsplit("/", 1)[-1].split(".", 1)[0]
                chapters.append(
                    ChapterInfoDict(
                        title=title,
                        url=href,
                        chapterId=chapter_id,
                    )
                )

        if not chapters:
            return None

        volumes: list[VolumeInfoDict] = [
            VolumeInfoDict(volume_name="正文", chapters=chapters)
        ]

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

        title: str = ""
        paragraphs: list[str] = []

        for h in html_list:
            tree = html.fromstring(h)
            if not title:
                title = self._first_str(tree.xpath('//h1[@id="chapterTitle"]/text()'))

            paragraphs.extend(
                c
                for s in tree.xpath('//div[@id="content"]//p//text()')
                if (
                    c := s.replace("&emsp;", "")
                    .replace("&esp;", "")
                    .replace("\xa0", "")
                    .strip()
                )
            )

        if not paragraphs:
            return None

        content = "\n".join(paragraphs)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
