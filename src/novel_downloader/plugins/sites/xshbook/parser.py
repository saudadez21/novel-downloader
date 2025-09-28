#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.xshbook.parser
---------------------------------------------

"""

import re
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
class XshbookParser(BaseParser):
    """Parser for 小说虎 book pages."""

    site_name: str = "xshbook"
    BASE = "http://www.xshbook.com"

    ADS = {
        r"谨记我们的网址",
        r"温馨提示",
        r"^提示.{0,50}$",  # "提示" 开头且内容较短
        r"^分享.{0,40}$",  # "分享" 开头且内容较短
    }
    # Inline ads like “本文搜：xxx.com 免费阅读”
    _INLINE_AD_PATTERN = re.compile(
        r"(本文搜|搜索[:：]?)\s*.*?\s*(免费阅读|本文免费阅读)"
    )  # noqa: E501

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        book_name = self._first_str(tree.xpath("//div[@id='info']/h1/text()"))

        author = self._first_str(
            tree.xpath("//div[@id='info']/p[1]/text()"),
            replaces=[("\xa0", ""), ("作者:", "")],
        )

        update_time = self._first_str(
            tree.xpath("//meta[@property='og:novel:update_time']/@content")
        )

        summary = "\n".join(
            self._first_str(p.xpath("string()").splitlines())
            for p in tree.xpath("//div[@id='intro']//p")
        ).strip()
        summary = summary.split("本站提示", 1)[0].strip()

        cover_url = self._first_str(tree.xpath("//div[@id='fmimg']//img/@src"))

        book_type = self._first_str(tree.xpath("//div[@class='con_top']/a[2]/text()"))
        tags: list[str] = [book_type] if book_type else []

        chapters: list[ChapterInfoDict] = []
        for a in tree.xpath("//div[@id='list']//dd/a"):
            href = a.get("href", "")
            title = self._norm_space(a.text_content())
            # /95071/95071941/389027455.html -> "389027455"
            chapter_id = href.rsplit("/", 1)[-1].split(".", 1)[0]
            chapters.append({"title": title, "url": href, "chapterId": chapter_id})

        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

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

        title = self._first_str(tree.xpath("//div[@class='bookname']/h1/text()"))
        if not title:
            title = self._first_str(
                tree.xpath("//div[@class='con_top']/text()[last()]")
            )

        paragraphs: list[str] = []
        for p in tree.xpath("//div[@id='content']//p"):
            text = self._norm_space(p.text_content() or "")
            text = self._INLINE_AD_PATTERN.sub("", text).strip()
            if not text or self._is_ad_line(text):
                continue
            paragraphs.append(text)

        content = "\n".join(paragraphs)
        if not content.strip():
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
