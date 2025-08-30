#!/usr/bin/env python3
"""
novel_downloader.core.parsers.biquyuedu
---------------------------------------

"""

from typing import Any

from lxml import etree, html

from novel_downloader.core.parsers.base import BaseParser
from novel_downloader.core.parsers.registry import register_parser
from novel_downloader.models import (
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    VolumeInfoDict,
)


@register_parser(
    site_keys=["biquyuedu"],
)
class BiquyueduParser(BaseParser):
    """
    Parser for 精彩小说 book pages.
    """

    ADS: set[str] = {
        "笔趣阁",
        "请记住本书首发域名",
        "www.biquyuedu.com",
    }

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        # --- Metadata ---
        book_name = self._first_str(tree.xpath("//div[@class='info']/h1/text()"))
        author = self._first_str(
            tree.xpath(
                "//div[@class='info']//div[@class='small'][1]//span[1]//a/text()"
            )
        )
        cover_url = self._first_str(
            tree.xpath("//div[@class='info']//div[@class='cover']//img/@src")
        )
        update_time = self._first_str(
            tree.xpath("//div[@class='info']//div[@class='small'][2]//span[1]/text()"),
            replaces=[("更新时间：", "")],
        )

        crumbs = tree.xpath("//div[@class='path']//div[@class='p']/a/text()")
        book_type = self._first_str(crumbs[1:2])
        tags = [book_type] if book_type else []

        intro_text = tree.xpath(
            "string(//div[@class='info']//div[@class='intro'])"
        ).strip()
        summary = intro_text.replace("简介：", "", 1).split("作者：", 1)[0].strip()

        # --- Chapters ---
        chapters: list[ChapterInfoDict] = [
            {
                "title": (a.get("title") or a.text_content() or "").strip(),
                "url": (a.get("href") or "").strip(),
                "chapterId": (a.get("href") or "").rsplit("/", 1)[-1].split(".", 1)[0],
            }
            for a in tree.xpath(
                "//div[@class='listmain']//dl/dd[preceding-sibling::dt[1][contains(text(),'全文')]]/a"
            )
        ]

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

        # Extract chapter title via helper
        title = self._first_str(tree.xpath("//div[@class='content']/h1/text()"))

        # Find the main content container
        content_nodes = tree.xpath("//div[@id='content']")
        if not content_nodes:
            return None
        content_div = content_nodes[0]

        etree.strip_elements(content_div, "script", with_tail=False)
        raw_texts = content_div.xpath(".//text()[normalize-space()]")

        # Clean & filter in one comprehension
        paragraphs = [
            txt.replace("\xa0", "").strip()
            for txt in raw_texts
            if not self._is_ad_line(txt)
        ]

        content = "\n".join(paragraphs)
        if not content.strip():
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": "biquyuedu"},
        }
