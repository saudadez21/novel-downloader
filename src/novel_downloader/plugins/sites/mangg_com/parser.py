#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.mangg_com.parser
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
class ManggComParser(BaseParser):
    """
    Parser for 追书网 book pages.
    """

    site_name: str = "mangg_com"
    BASE_URL = "https://www.mangg.com"
    ADS: set[str] = {
        "记住追书网网",
        r"mangg\.com",
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
        book_name = self._first_str(tree.xpath('//div[@id="info"]/h1/text()'))
        author = self._first_str(
            tree.xpath('//div[@id="info"]/p[1]/text()'),
            replaces=[(chr(0xA0), ""), ("作者：", "")],
        )
        serial_status = self._first_str(
            tree.xpath('//div[@id="info"]/p[2]/text()'),
            replaces=[(chr(0xA0), ""), ("状态：", ""), (",", "")],
        )
        update_time = self._first_str(
            tree.xpath('//div[@id="info"]/p[3]/text()'),
            replaces=[("最后更新：", "")],
        )

        cover_src = self._first_str(tree.xpath('//div[@id="sidebar"]//img/@src'))
        cover_url = (
            cover_src if cover_src.startswith("http") else f"{self.BASE_URL}{cover_src}"
        )

        summary = self._join_strs(
            tree.xpath('//div[@id="intro"]/text() | //div[@id="intro"]//p/text()'),
            replaces=[(chr(0xA0), "")],
        )

        # --- Volumes & Chapters ---
        chapters: list[ChapterInfoDict] = [
            {
                "title": (a.text or "").strip(),
                "url": (a.get("href") or "").strip(),
                "chapterId": (a.get("href") or "").rsplit("/", 1)[-1].split(".", 1)[0],
            }
            for a in tree.xpath('//div[@id="list"]//dd/a')
        ]
        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "serial_status": serial_status,
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

        title = self._first_str(tree.xpath('//div[@class="bookname"]/h1/text()'))

        lines: list[str] = []
        for ln in tree.xpath(
            '//div[@id="content"]//text()[not(ancestor::script) and not(ancestor::style)]'  # noqa: E501
        ):
            if not ln or not ln.strip() or self._is_ad_line(ln):
                continue
            lines.append(ln.strip())

        content = "\n".join(lines)
        if not content.strip():
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
