#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.westnovel.parser
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
class WestnovelParser(BaseParser):
    """
    Parser for 西方奇幻小说网 book pages.
    """

    site_name: str = "westnovel"
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
        book_name = self._first_str(tree.xpath('//div[@class="btitle"]/h1/a/text()'))
        author = self._first_str(
            tree.xpath('//div[@class="btitle"]/em/text()'), [("作者：", "")]
        )

        cover_url = self._first_str(
            tree.xpath('//div[@class="bookinfo"]//img[@class="img-img"]/@src')
        )
        cover_url = self.BASE_URL + cover_url if cover_url else ""

        summary_nodes = tree.xpath(
            '//div[@class="intro"]/span[@class="intro-p"]//p//text()'
        )
        summary = self._join_strs(summary_nodes, [("内容简介：", "")])

        # Chapter volumes & listings
        chapters: list[ChapterInfoDict] = []
        for a in tree.xpath('//dl[@class="chapterlist"]//dd/a'):
            href = a.get("href")
            title = a.text_content().strip()
            if not href or not title:
                continue

            # Example href: /wuxia/ynyh/198246.html
            chapter_id = href.rsplit("/", 1)[-1].split(".", 1)[0]
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
        title = self._first_str(tree.xpath('//div[@id="BookCon"]/h1/text()'))

        # Content paragraphs
        paragraphs: list[str] = [
            text
            for p in tree.xpath('//div[@id="BookText"]//p')
            if (text := p.text_content().strip())
        ]
        if not paragraphs:
            raw = tree.xpath('//div[@id="BookText"]//text()')
            paragraphs = [s.strip() for s in raw if s.strip()]

        if not paragraphs:
            return None

        content = "\n".join(paragraphs)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
