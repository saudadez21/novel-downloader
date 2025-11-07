#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.westnovel_sub.parser
---------------------------------------------------
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
class WestnovelSubParser(BaseParser):
    """
    Parser for 西方奇幻小说网 book pages.
    """

    site_name: str = "westnovel_sub"
    BASE_URL = "https://www.westnovel.com"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        # Book metadata
        book_name = self._first_str(tree.xpath('//div[@id="bookinfo"]//h1/text()'))
        author = self._first_str(
            tree.xpath(
                '//div[@id="count"]//li[strong[contains(text(), "作者")]]//a/text()'
            )
        )

        cover_url = self._first_str(tree.xpath('//div[@id="bookimg"]//img/@src'))
        cover_url = self.BASE_URL + cover_url if cover_url else ""

        summary_nodes = tree.xpath('//div[@id="bookintro"]//text()')
        summary = self._join_strs(summary_nodes)

        # Chapter volumes & listings
        chapters: list[ChapterInfoDict] = []
        for a in tree.xpath('//ul[@id="chapterList"]//a'):
            href = a.get("href")
            title = a.text_content().strip()
            if not href or not title:
                continue

            # Example href: /q/showinfo-2-22999-0.html
            chapter_id = (
                href.rsplit("/", 1)[-1].split(".", 1)[0].replace("showinfo-", "")
            )
            chapters.append(
                {
                    "title": title,
                    "url": href,
                    "chapterId": chapter_id,
                }
            )

        if not chapters:
            return None

        volumes: list[VolumeInfoDict] = [
            {
                "volume_name": "正文",
                "chapters": chapters,
            }
        ]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": "",
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

        # Title
        title = self._first_str(tree.xpath('//div[@id="mlfy_main_text"]/h1/text()'))

        # Content paragraphs
        paragraphs: list[str] = [
            text
            for p in tree.xpath('//div[@id="TextContent"]//p')
            if (text := p.text_content().strip())
        ]
        if not paragraphs:
            raw_texts = tree.xpath('//div[@id="TextContent"]//text()')
            paragraphs = [t.strip() for t in raw_texts if t.strip()]

        if not paragraphs:
            return None

        content = "\n".join(paragraphs)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
