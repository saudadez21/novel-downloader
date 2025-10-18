#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.guidaye.parser
---------------------------------------------

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
class GuidayeParser(BaseParser):
    """
    Parser for 名著阅读 book pages.
    """

    site_name: str = "guidaye"

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
            tree.xpath('//meta[@property="og:novel:book_name"]/@content')
        )
        author = self._first_str(
            tree.xpath('//meta[@property="og:novel:author"]/@content')
        )
        cover_url = self._first_str(tree.xpath('//meta[@property="og:image"]/@content'))
        update_time = self._first_str(
            tree.xpath('//meta[@property="og:novel:update_time"]/@content')
        )
        category = self._first_str(
            tree.xpath('//meta[@property="og:novel:category"]/@content')
        )
        summary = self._first_str(
            tree.xpath('//meta[@property="og:description"]/@content')
        )
        tags = [category] if category else []

        # Chapter volumes & listings
        chapters: list[ChapterInfoDict] = []
        for a in tree.xpath('//ol[@id="list-ol"]//a'):
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
        volumes: list[VolumeInfoDict] = [
            VolumeInfoDict(volume_name="正文", chapters=chapters)
        ]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
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
        tree = html.fromstring(html_list[0])
        article = tree.xpath('//article[@class="article-post"]')
        if not article:
            return None
        article = article[0]

        # Title from entry-title
        title = self._first_str(
            tree.xpath(
                '//h1[contains(@class,"secondfont") or @class="entry-title"]/text()'
            )
        )

        # Extract paragraphs within entry-content
        paragraphs: list[str] = []
        if article.text and (text := article.text.strip()):
            paragraphs.append(text)
        for node in article.xpath(".//*"):
            if node.text and (text := node.text.strip()):
                paragraphs.append(text)
            if node.tail and (tail := node.tail.strip()):
                paragraphs.append(tail)

        if not paragraphs:
            return None

        content = "\n".join(paragraphs)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
