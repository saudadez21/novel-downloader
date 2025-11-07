#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.akatsuki_novels.parser
-----------------------------------------------------
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
class AkatsukiNovelsParser(BaseParser):
    """
    Parser for 暁 book pages.
    """

    site_name: str = "akatsuki_novels"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        book_name = self._first_str(tree.xpath('//h3[@class="font-bb"]/a/text()'))
        author = self._first_str(
            tree.xpath('//h3[@class="font-bb"][contains(., "作者")]/a/text()')
        )
        summary = self._join_strs(
            tree.xpath(
                '//div[contains(normalize-space(@class), "body-x1 body-normal body-w640")]/div/div[1]//text()'  # noqa: E501
            )
        )

        # Chapters
        chapters: list[ChapterInfoDict] = []
        for a in tree.xpath('//table[@class="list"]//tbody//tr/td[1]/a'):
            url = a.get("href", "").strip()
            if not url:
                continue
            # /stories/view/1471/novel_id~103 -> "1471"
            parts = url.split("/")
            chapter_id = parts[3] if len(parts) > 3 else ""
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
            "cover_url": "",
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

        title = self._first_str(tree.xpath("//h2/text()"))

        paragraphs = [
            s
            for p in tree.xpath('//div[@class="body-novel"]//text()')
            if (s := p.strip())
        ]

        if not paragraphs:
            return None

        content = "\n".join(paragraphs)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
