#!/usr/bin/env python3
"""
novel_downloader.core.parsers.quanben5
--------------------------------------

"""

import re
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
    site_keys=["quanben5"],
)
class Quanben5Parser(BaseParser):
    """Parser for 全本小说网 book pages."""

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        """
        Parse a book info page and extract metadata and chapter structure.

        :param html_list: Raw HTML of the book info page.
        :return: Parsed metadata and chapter structure as a dictionary.
        """
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
            match = re.search(r"/(\d+)\.html$", href)
            chapter_id = match.group(1) if match else ""
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
        """
        Parse a single chapter page and extract clean text or simplified HTML.

        :param html_list: Raw HTML of the chapter page.
        :param chapter_id: Identifier of the chapter being parsed.
        :return: Cleaned chapter content as plain text or minimal HTML.
        """
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        # Extract the chapter title
        title = self._first_str(tree.xpath('//h1[@class="title1"]/text()'))

        # Extract all <p> text within the content container
        paragraphs = tree.xpath('//div[@id="content"]/p/text()')
        # Clean whitespace and join with double newlines
        content = "\n\n".join(p.strip() for p in paragraphs if p.strip())

        if not content:
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": "quanben5"},
        }
