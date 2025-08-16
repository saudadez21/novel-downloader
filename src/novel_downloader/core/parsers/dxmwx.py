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
    """Parser for 大熊猫文学网 book pages."""

    X_BOOK_NAME = "//span[contains(@style,'font-size: 24px')]/text()"
    X_AUTHOR = "//div[contains(@style,'height: 28px') and contains(., '著')]//a/text()"
    X_TAGS = "//span[@class='typebut']//a/text()"
    X_COVER = "//img[@class='imgwidth']/@src"
    X_SUMMARY_NODE = (
        "//div[contains(@style,'min-height') and "
        "contains(@style,'padding-left') and contains(@style,'padding-right')][1]"
    )
    X_UPDATE = (
        "normalize-space(string(//span[starts-with(normalize-space(.), '更新时间：')]))"
    )

    X_CHAPTER_ANCHORS = (
        "//div[contains(@style,'height:40px') and contains(@style,'border-bottom')]//a"
    )

    X_TITLE = "//h1[@id='ChapterTitle']/text()"
    X_CONTENT_P = "//div[@id='Lab_Contents']//p"

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

        info_tree = html.fromstring(html_list[0])
        catalog_tree = html.fromstring(html_list[1])

        book_name = self._first_str(info_tree.xpath(self.X_BOOK_NAME))
        author = self._first_str(info_tree.xpath(self.X_AUTHOR))
        tags = [t.strip() for t in info_tree.xpath(self.X_TAGS) if t.strip()]
        cover_url = self._abs_url(self._first_str(info_tree.xpath(self.X_COVER)))

        raw = info_tree.xpath(self.X_UPDATE)
        update_time = self.normalize_update_date(raw.replace("更新时间：", "").strip())

        summary = self._extract_summary(info_tree)

        chapters = self._extract_chapters(catalog_tree)
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
        title = re.sub(r"\s+", " ", title).strip()

        paragraphs: list[str] = []
        for p in tree.xpath(self.X_CONTENT_P):
            text = self._clean_spaces(p.text_content())
            if not text:
                continue  # skips <p/> spacers and empty lines
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

    @staticmethod
    def _clean_spaces(s: str) -> str:
        s = s.replace("\xa0", " ")
        s = re.sub(r"[ \t\u3000]+", " ", s)
        s = re.sub(r"\n{2,}", "\n", s)
        return s.strip()

    @staticmethod
    def _chapter_id_from_href(href: str) -> str:
        # "/read/57215_50197663.html" -> "50197663"
        return href.split("read/", 1)[-1].split(".html", 1)[0].split("_")[-1]

    @staticmethod
    def _abs_url(url: str) -> str:
        # Site uses absolute paths like "/images/..".
        if url.startswith("http://") or url.startswith("https://"):
            return url
        if url.startswith("/"):
            return "https://www.dxmwx.org" + url
        return url

    def _extract_summary(self, info_tree: html.HtmlElement) -> str:
        """
        Extract the entire summary block.
        """
        nodes = info_tree.xpath(self.X_SUMMARY_NODE)
        if not nodes:
            return ""
        texts = [t.replace("\xa0", " ").strip() for t in nodes[0].xpath(".//text()")]
        lines = [t for t in texts if t]
        text = "\n".join(lines)
        # normalize
        text = re.sub(r"^\s*[:：]\s*", "", text)
        return self._clean_spaces(text)

    def _extract_chapters(
        self, catalog_tree: html.HtmlElement
    ) -> list[ChapterInfoDict]:
        chapters: list[ChapterInfoDict] = []
        for a in catalog_tree.xpath(self.X_CHAPTER_ANCHORS):
            href = a.get("href") or ""
            title = (a.text_content() or "").strip()
            if not href or not title:
                continue
            chap_id = self._chapter_id_from_href(href)
            chapters.append({"title": title, "url": href, "chapterId": chap_id})
        return chapters

    @staticmethod
    def normalize_update_date(raw: str) -> str:
        """
        Return a YYYY-MM-DD string.
        1) If raw contains a 'YYYY-MM-DD', return it.
        2) Otherwise, fall back to today's date (local) as 'YYYY-MM-DD'.
        """
        if not raw:
            return datetime.now().strftime("%Y-%m-%d")
        m = re.search(r"\d{4}-\d{2}-\d{2}", raw)
        if m:
            return m.group(0)
        return datetime.now().strftime("%Y-%m-%d")
