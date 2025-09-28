#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.zhenhunxiaoshuo.parser
-----------------------------------------------------

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
class ZhenhunxiaoshuoParser(BaseParser):
    """
    Parser for 镇魂小说网 book pages.
    """

    site_name: str = "zhenhunxiaoshuo"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        book_name = self._first_str(
            tree.xpath("//h1[contains(@class,'focusbox-title')]/text()")
        )
        update_time = datetime.now().strftime("%Y-%m-%d")
        summary = self._join_strs(
            tree.xpath(
                "//div[contains(@class,'focusbox-text')]//p[contains(@class,'text')]//text()"
            ),
            replaces=[("\u3000", " ")],
        )

        chapters: list[ChapterInfoDict] = [
            {
                "title": (a.text or "").strip(),
                "url": (a.get("href") or "").strip(),
                "chapterId": (a.get("href") or "").rsplit("/", 1)[-1].split(".", 1)[0],
            }
            for a in tree.xpath("//div[contains(@class,'excerpts')]//article//a[@href]")
        ]

        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": "",
            "cover_url": "",
            "update_time": update_time,
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
            tree.xpath(
                "//header[contains(@class,'article-header')]//h1[contains(@class,'article-title')]/text()"
            )
        )

        paragraphs = [
            (p.text or "").strip()
            for p in tree.xpath("//article[contains(@class,'article-content')]//p")
            if (p.text or "").strip()
        ]
        content = "\n".join(paragraphs)
        if not content:
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
