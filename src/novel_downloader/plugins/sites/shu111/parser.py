#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.shu111.parser
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
class Shu111Parser(BaseParser):
    """
    Parser for 书林文学 book pages.
    """

    site_name: str = "shu111"

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
            or tree.xpath('//meta[@property="og:title"]/@content')
            or tree.xpath('//h1[contains(@class, "bookTitle")]/text()')
        )
        author = self._first_str(
            tree.xpath('//meta[@property="og:novel:author"]/@content')
            or tree.xpath(
                '//p[contains(@class,"booktag")]//a[contains(@href, "authorarticle")]/text()'  # noqa: E501
            )
        )
        cover_url = self._first_str(
            tree.xpath('//meta[@property="og:image"]/@content')
            or tree.xpath('(//img[contains(@class,"img-thumbnail")]/@src)[1]')
        )
        update_time = self._first_str(
            tree.xpath('//meta[@property="og:novel:update_time"]/@content')
            or tree.xpath('//p[contains(.,"最新章节")]//span/text()')
            or tree.xpath('//p[contains(.,"更新时间")]/text()'),
            replaces=[("（", ""), ("）", ""), ("更新时间：", "")],
        )
        serial_status = self._first_str(
            tree.xpath('//meta[@property="og:novel:status"]/@content')
            or tree.xpath('//p[contains(@class,"booktag")]/span[last()]/text()')
        )
        word_count = self._first_str(
            tree.xpath(
                '//p[contains(@class,"booktag")]//span[contains(.,"字数")]/text()'
            ),
            replaces=[("字数：", "")],
        )

        summary = self._first_str(
            tree.xpath('//meta[@property="og:description"]/@content')
        )
        if not summary:
            summary = self._join_strs(
                tree.xpath('//p[@id="bookIntro"]//text()'), replaces=[("\xa0", " ")]
            )

        book_type = self._first_str(
            tree.xpath('//meta[@property="og:novel:category"]/@content')
            or tree.xpath(
                '//p[contains(@class,"booktag")]//a[contains(@href,"/list/")]/text()'
            )
            or tree.xpath('//ol[contains(@class,"breadcrumb")]//li[2]/a/text()')
        )
        tags = [book_type] if book_type else []

        chapters: list[ChapterInfoDict] = [
            {
                "title": (a.text or "").strip(),
                "url": (a.get("href") or "").strip(),
                "chapterId": (a.get("href") or "").rsplit("/", 1)[-1].split(".", 1)[0],
            }
            for a in tree.xpath('//*[@id="list-chapterAll"]//dd/a')
        ]

        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "serial_status": serial_status,
            "word_count": word_count,
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

        title = self._first_str(
            tree.xpath('//h1[contains(@class,"readTitle")]/text()'),
            replaces=[("\xa0", " ")],
        )

        paragraphs: list[str] = []
        for node in tree.xpath('//div[@id="htmlContent"]//text()'):
            line = node.replace("\xa0", " ").strip()
            if line:
                paragraphs.append(line)

        content = "\n".join(paragraphs)
        if not content.strip():
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
