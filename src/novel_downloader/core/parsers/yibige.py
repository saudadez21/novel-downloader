#!/usr/bin/env python3
"""
novel_downloader.core.parsers.yibige
------------------------------------

"""

import re
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
    site_keys=["yibige"],
)
class YibigeParser(BaseParser):
    """Parser for 一笔阁 book pages."""

    X_TITLE = "//div[@class='bookname']/h1/text()"
    X_P_NODES = "//div[@id='content']//p"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        """
        Parse a book info page and extract metadata and chapter structure.

        :param html_list: Raw HTML of the book info page.
        :return: Parsed metadata and chapter structure as a dictionary.
        """
        if len(html_list) < 2:
            return None

        # Parse trees
        info_tree = html.fromstring(html_list[0])
        catalog_tree = html.fromstring(html_list[1])

        # --- Basic metadata (single XPath each) ---
        book_name = self._first_str(info_tree.xpath("//div[@id='info']/h1/text()"))
        author = self._first_str(info_tree.xpath("//div[@id='info']/p[a]/a/text()"))
        cover_url = self._first_str(info_tree.xpath("//div[@id='fmimg']//img/@src"))

        # Time + status line like: "时间：2025-04-09 22:42:42 连载中"
        time_line = self._first_str(
            info_tree.xpath("//div[@id='info']/p[contains(., '时间：')]/text()")
        )
        m_time = re.search(r"(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2}:\d{2})?)", time_line)
        update_time = m_time.group(1) if m_time else ""
        m_status = re.search(r"(连载中|已完结|完结)", time_line)
        serial_status = m_status.group(1) if m_status else "连载中"

        word_count = self._first_str(
            info_tree.xpath("//div[@id='info']/p[contains(., '字数：')]/text()[1]"),
            replaces=[("字数：", "")],
        )

        # Summary: first paragraph under #intro
        summary = self._first_str(info_tree.xpath("//div[@id='intro']//p[1]/text()"))

        # Tags/Category: breadcrumb second link
        book_type = self._first_str(
            info_tree.xpath("//div[@class='con_top']/a[2]/text()")
        )
        tags = [book_type] if book_type else []

        # --- Chapters from the catalog page ---
        chapters = self._extract_chapters(catalog_tree)

        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "serial_status": serial_status,
            "word_count": word_count,
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
        """
        Parse a single chapter page and extract clean text or simplified HTML.

        :param html_list: Raw HTML of the chapter page.
        :param chapter_id: Identifier of the chapter being parsed.
        :return: Cleaned chapter content as plain text or minimal HTML.
        """
        if not html_list:
            return None
        tree = html.fromstring(html_list[0])

        title = self._first_str(tree.xpath(self.X_TITLE))

        paragraphs: list[str] = []
        for p in tree.xpath(self.X_P_NODES):
            txt = self._clean_text(p.text_content())
            if not txt or self._is_ad(txt):
                continue
            paragraphs.append(txt)

        content = "\n".join(paragraphs).strip()
        if not content:
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": "yibige"},
        }

    def _extract_chapters(
        self, catalog_tree: html.HtmlElement
    ) -> list[ChapterInfoDict]:
        """
        Grab every chapter link under #list > dl > dd > a, and compute chapterId.
        """
        chapters: list[ChapterInfoDict] = []
        for a in catalog_tree.xpath("//div[@id='list']/dl/dd/a"):
            href = (a.get("href") or "").strip()
            if not href:
                continue
            title = (a.text_content() or "").strip()
            if not title:
                continue
            chap_id = self._chapter_id_from_href(href)
            chapters.append({"title": title, "url": href, "chapterId": chap_id})
        return chapters

    @staticmethod
    def _chapter_id_from_href(href: str) -> str:
        """
        /6238/2496.html -> 2496
        /1921/1.html    -> 1
        """
        last = href.strip("/").split("/")[-1]
        return last.split(".")[0]

    @staticmethod
    def _clean_text(s: str) -> str:
        """Normalize whitespace and remove zero-width/nbsp."""
        if not s:
            return ""
        s = (
            s.replace("\xa0", " ")
            .replace("\u200b", "")
            .replace("\ufeff", "")
            .replace("\u3000", " ")
        )
        s = re.sub(r"[ \t]+", " ", s)  # collapse spaces/tabs
        return s.strip()

    @staticmethod
    def _is_ad(s: str) -> bool:
        """Very small heuristic filter for footer junk inside #content."""
        bad = [
            "首发无广告",
            "请分享",
            "读之阁",
            "小说网",
            "首发地址",
            "手机阅读",
            "一笔阁",
            "site_con_ad(",
            "chapter_content(",
        ]
        ss = s.replace(" ", "")
        return any(b in s or b in ss for b in bad)
