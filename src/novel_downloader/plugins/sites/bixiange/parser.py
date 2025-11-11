#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.bixiange.parser
----------------------------------------------
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
class BixiangeParser(BaseParser):
    """
    Parser for 笔仙阁 book pages.
    """

    site_name: str = "bixiange"
    BASE_URL = "https://m.bixiange.me"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        # --- Basic Metadata ---
        book_name = self._first_str(tree.xpath('//div[@class="desc"]/h1/text()'))
        author = self._first_str(
            tree.xpath(
                '//div[@class="descTip"]//span[contains(text(), "作者")]/text()'
            ),  # noqa: E501
            replaces=[("作者：", "")],
        )
        cover_url = self._first_str(tree.xpath('//div[@class="cover"]/img/@src'))
        if cover_url.startswith("//"):
            cover_url = "https:" + cover_url
        elif cover_url.startswith("/"):
            cover_url = self.BASE_URL + cover_url

        update_time = self._first_str(
            tree.xpath(
                '//div[@class="descTip"]//span[contains(text(), "时间")]/text()'
            ),  # noqa: E501
            replaces=[("时间：", "")],
        )

        genre = self._first_str(
            tree.xpath(
                '//div[@class="descTip"]//span[contains(text(), "分类")]/text()'
            ),  # noqa: E501
            replaces=[("分类：", "")],
        )
        tags = [genre] if genre else []

        summary = self._join_strs(tree.xpath('//div[@class="descInfo"]//text()'))

        # --- Volumes & Chapters ---
        chapters: list[ChapterInfoDict] = []
        for a in tree.xpath('//div[contains(@class, "catalog")]//a'):
            href = a.get("href", "").strip()
            if not href:
                continue

            chapter_id = href.rsplit("/", 1)[-1].split(".", 1)[0]
            title = a.text_content().strip()
            chapters.append(
                {
                    "title": title,
                    "url": href,
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
            tree.xpath('//div[contains(@class, "article")]//h1/text()')
        )

        paragraphs = [
            s for p in tree.xpath('//div[@id="mycontent"]//text()') if (s := p.strip())
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
