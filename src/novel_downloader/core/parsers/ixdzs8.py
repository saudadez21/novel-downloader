#!/usr/bin/env python3
"""
novel_downloader.core.parsers.ixdzs8
------------------------------------

"""

import contextlib
import json
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
    site_keys=["ixdzs8"],
)
class Ixdzs8Parser(BaseParser):
    """
    Parser for 爱下电子书 book pages.
    """

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
        if len(html_list) < 2 or not html_list[0] or not html_list[1]:
            return None

        # Parse HTML
        tree = html.fromstring(html_list[0])

        book_id = ""
        hrefs = tree.xpath("//a/@href") + tree.xpath(
            "//link[@property='og:novel:read_url']/@content"
        )
        for h in hrefs:
            m = re.search(r"/read/(\d+)(?:/|$)", h)
            if m:
                book_id = m.group(1)
                break

        book_name = self._clean_text(
            "".join(tree.xpath("//div[@class='n-text']/h1/text()"))
        )
        author = self._clean_text(
            "".join(
                tree.xpath(
                    "//div[@class='n-text']/p[a[contains(@class,'bauthor')]]/a/text()"
                )
            )
        )
        cover_url = self._clean_text(
            "".join(tree.xpath("//div[@class='n-img']//img/@src"))
        )

        category = self._clean_text(
            "".join(
                tree.xpath(
                    "//div[@class='n-text']/p[a[contains(@class,'nsort')]]/a/text()"
                )
            )
        )
        serial_status = self._clean_text(
            "".join(
                tree.xpath(
                    "//div[@class='n-text']/p[a[contains(@class,'nsort')]]/span/text()"
                )
            )
        )

        word_count = self._clean_text(
            "".join(
                tree.xpath(
                    "//div[@class='n-text']//span[contains(@class,'nsize')]/text()"
                )
            )
        )

        update_time = self._clean_text(
            "".join(
                tree.xpath(
                    "//div[@class='n-text']/p[starts-with(normalize-space(),'最新:')]/following-sibling::p[1]/text()"
                )
            )
        )
        if update_time.startswith("更新:"):
            update_time = update_time.replace("更新:", "", 1).strip()
        if not update_time:
            update_time = self._clean_text(
                "".join(tree.xpath("//meta[@property='og:novel:update_time']/@content"))
            )

        intro_node = tree.xpath("//p[@id='intro' or contains(@class,'pintro')]")
        if intro_node:
            summary_raw = intro_node[0].text_content()
        else:
            summary_raw = "".join(
                tree.xpath("//meta[@property='og:description']/@content")
            )
        summary = self._clean_text(summary_raw)

        tags = []
        if category:
            tags.append(category)
        tags.extend(
            [
                self._clean_text(t)
                for t in tree.xpath("//div[contains(@class,'tags')]//em/a/text()")
            ]
        )

        data = {}
        with contextlib.suppress(Exception):
            data = json.loads(html_list[1])
        clist = data.get("data", []) if isinstance(data, dict) else []

        chapters: list[ChapterInfoDict] = []
        for chap in clist:
            ordernum = str(chap.get("ordernum", "")).strip()
            if not ordernum:
                continue
            title = self._clean_text(chap.get("title", "") or "")
            url = f"/read/{book_id}/p{ordernum}.html" if book_id else ""
            chapters.append(
                {
                    "url": url,
                    "title": title or "未命名章节",
                    "chapterId": f"p{ordernum}",
                }
            )

        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "serial_status": serial_status,
            "update_time": update_time,
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

        title = ""
        for xp in (
            "//div[@class='page-d-top']/h1/text()",
            "//article[contains(@class,'page-content')]//h3/text()",
            "string(//title)",
        ):
            t = "".join(tree.xpath(xp)).strip()
            if t:
                if xp == "string(//title)":
                    # Strip site suffix (e.g., "_书名-站点")
                    t = re.split(r"[_|\-—]", t, maxsplit=1)[0].strip()
                title = self._clean_text(t)
                break

        # Collect content paragraphs within the reading section (skip ads)
        ps = tree.xpath(
            "//article[contains(@class,'page-content')]//section//p[not(contains(@class,'abg'))]"
        )

        paragraphs: list[str] = []
        for p in ps:
            txt = p.text_content()
            txt = self._clean_text(txt)
            if txt:
                paragraphs.append(txt)

        if not paragraphs:
            return None

        # 1) Replace FIRST line with .replace(title, "")
        first = paragraphs[0].replace(title, "")
        first = first.replace(title.replace(" ", ""), "").strip()
        if first:
            paragraphs[0] = first
        else:
            paragraphs.pop(0)

        if paragraphs:
            last = paragraphs[-1]
            if ("(本章完)" in last) or ("（本章完）" in last):
                paragraphs.pop()

        content = "\n".join(paragraphs)
        if not content.strip():
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": "ixdzs8"},
        }

    @staticmethod
    def _clean_text(s: str) -> str:
        # Collapse whitespace and HTML artifacts.
        s = s.replace("\xa0", " ").replace("\u3000", " ")
        s = re.sub(r"\s+", " ", s, flags=re.S).strip()
        return s
