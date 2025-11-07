#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.czbooks.parser
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
class CzbooksParser(BaseParser):
    """
    Parser for 小说狂人 book pages.
    """

    site_name: str = "czbooks"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        book_name = self._first_str(
            tree.xpath("//div[contains(@class,'info')]//span[@class='title']/text()")
        )
        author = self._first_str(
            tree.xpath(
                "//div[contains(@class,'info')]//span[@class='author']//a/text()"
            )
        )
        cover_url = self._first_str(
            tree.xpath("//div[contains(@class,'thumbnail')]//img/@src")
        )
        if cover_url.startswith("//"):
            cover_url = "https:" + cover_url

        update_time = self._first_str(
            tree.xpath(
                "//div[contains(@class,'state')]//tr[normalize-space(td[1])='更新時間']/td[2]/text()"
            )
        )
        serial_status = self._first_str(
            tree.xpath(
                "//div[contains(@class,'state')]//tr[normalize-space(td[1])='連載狀態']/td[2]/text()"
            )
        )

        genre = self._first_str(tree.xpath("//a[@id='novel-category']/text()"))
        tags = [genre] if genre else []

        summary = self._join_strs(
            tree.xpath("//div[contains(@class,'description')]//text()")
        )

        # Chapters from the book_list
        chapters: list[ChapterInfoDict] = []
        for a in tree.xpath("//ul[@id='chapter-list']//a"):
            url = a.get("href", "").strip()
            if not url:
                continue
            if url.startswith("//"):
                url = "https:" + url

            chapter_id = url.rsplit("/", 1)[-1].split("?", 1)[0]
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
            "serial_status": serial_status,
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

        title = self._first_str(tree.xpath("//div[contains(@class,'name')]/text()"))

        paragraphs = [  # from div class="content"
            s
            for p in tree.xpath("//div[contains(@class,'content')]//text()")
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
