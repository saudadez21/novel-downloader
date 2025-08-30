#!/usr/bin/env python3
"""
novel_downloader.core.parsers.dxmwx
-----------------------------------

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
    site_keys=["dxmwx"],
)
class DxmwxParser(BaseParser):
    """
    Parser for 大熊猫文学网 book pages.
    """

    _RE_DATE = re.compile(r"\d{4}-\d{2}-\d{2}")
    _RE_SPACES = re.compile(r"[ \t\u3000]+")
    _RE_NEWLINES = re.compile(r"\n{2,}")
    _RE_TITLE_WS = re.compile(r"\s+")

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if len(html_list) < 2:
            return None

        info_tree = html.fromstring(html_list[0])
        catalog_tree = html.fromstring(html_list[1])

        book_name = self._first_str(
            info_tree.xpath("//span[contains(@style,'font-size: 24px')]/text()")
        )
        author = self._first_str(
            info_tree.xpath(
                "//div[contains(@style,'height: 28px') and contains(., '著')]//a/text()"
            )
        )
        tags = [
            t.strip()
            for t in info_tree.xpath("//span[@class='typebut']//a/text()")
            if t.strip()
        ]
        cover_url = "https://www.dxmwx.org" + self._first_str(
            info_tree.xpath("//img[@class='imgwidth']/@src")
        )

        raw_update = self._first_str(
            info_tree.xpath(
                "normalize-space(string(//span[starts-with(normalize-space(.), '更新时间：')]))"  # noqa: E501
            )
        )
        raw_update = raw_update.replace("更新时间：", "").strip()
        update_time = self._normalize_update_date(raw_update)

        nodes = info_tree.xpath(
            "//div[contains(@style,'min-height') and "
            "contains(@style,'padding-left') and contains(@style,'padding-right')][1]"
        )
        summary = ""
        if nodes:
            texts = [
                t.replace("\xa0", " ").strip() for t in nodes[0].xpath(".//text()")
            ]
            lines = [t for t in texts if t]
            summary = "\n".join(lines)
            summary = re.sub(r"^\s*[:：]\s*", "", summary)
            summary = self._clean_spaces(summary)

        chapters: list[ChapterInfoDict] = []
        for a in catalog_tree.xpath(
            "//div[contains(@style,'height:40px') and contains(@style,'border-bottom')]//a"  # noqa: E501
        ):
            href = a.get("href") or ""
            title = (a.text_content() or "").strip()
            if not href or not title:
                continue
            # "/read/57215_50197663.html" -> "50197663"
            chap_id = href.split("read/", 1)[-1].split(".html", 1)[0].split("_")[-1]
            chapters.append({"title": title, "url": href, "chapterId": chap_id})
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

        title = self._first_str(tree.xpath("//h1[@id='ChapterTitle']/text()"))
        title = self._RE_TITLE_WS.sub(" ", title).strip()
        if not title:
            title = f"第 {chapter_id} 章"

        paragraphs: list[str] = []
        for p in tree.xpath("//div[@id='Lab_Contents']//p"):
            text = self._clean_spaces(p.text_content())
            if not text:
                continue
            if "点这里听书" in text or "大熊猫文学" in text:
                continue
            paragraphs.append(text)

        content = "\n".join(paragraphs).strip()
        if not content:
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": "dxmwx"},
        }

    @classmethod
    def _clean_spaces(cls, s: str) -> str:
        s = s.replace("\xa0", " ")
        s = cls._RE_SPACES.sub(" ", s)
        s = cls._RE_NEWLINES.sub("\n", s)
        return s.strip()

    @classmethod
    def _normalize_update_date(cls, raw: str) -> str:
        """Return a YYYY-MM-DD string."""
        if not raw:
            return datetime.now().strftime("%Y-%m-%d")
        m = cls._RE_DATE.search(raw)
        if m:
            return m.group(0)
        return datetime.now().strftime("%Y-%m-%d")
