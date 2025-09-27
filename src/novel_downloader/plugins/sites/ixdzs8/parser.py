#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ixdzs8.parser
--------------------------------------------

"""

import contextlib
import json
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
class Ixdzs8Parser(BaseParser):
    """
    Parser for 爱下电子书 book pages.
    """

    site_name: str = "ixdzs8"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if len(html_list) < 2 or not html_list[0] or not html_list[1]:
            return None

        # Parse HTML
        tree = html.fromstring(html_list[0])

        book_name = self._meta(tree, "og:novel:book_name") or self._first_str(
            tree.xpath("//div[@class='n-text']/h1/text()")
        )

        author = self._meta(tree, "og:novel:author") or self._first_str(
            tree.xpath("//div[@class='n-text']//a[contains(@class,'bauthor')]/text()")
        )

        cover_url = self._meta(tree, "og:image")
        if not cover_url:
            cover_url = self._first_str(tree.xpath("//div[@class='n-img']//img/@src"))

        serial_status = self._meta(tree, "og:novel:status")

        # 2022-08-25T18:08:03+08:00 -> 2022-08-25 18:08:03
        iso_time = self._meta(tree, "og:novel:update_time")
        update_time = ""
        if iso_time:
            update_time = iso_time.replace("T", " ").split("+", 1)[0].strip()

        word_count = self._first_str(
            tree.xpath("//div[@class='n-text']//span[contains(@class,'nsize')]/text()")
        )

        raw_summary = self._meta(tree, "og:description")
        summary = ""
        if raw_summary:
            s = raw_summary.replace("&nbsp;", "")
            s = s.replace("<br />", "\n")
            summary = "\n".join(
                self._norm_space(line) for line in s.splitlines()
            ).strip()

        tags = [
            self._norm_space(t)
            for t in tree.xpath("//div[contains(@class,'tags')]//em/a/text()")
            if t and t.strip()
        ]
        category = self._meta(tree, "og:novel:category") or self._first_str(
            tree.xpath("//div[@class='n-text']/p[a[contains(@class,'nsort')]]/a/text()")
        )
        if category:
            tags.append(category)

        book_path = self._meta(tree, "og:novel:read_url") or self._meta(tree, "og:url")
        book_id = ""
        if book_path:
            book_id = book_path.strip("/").split("/")[-1]

        data = {}
        with contextlib.suppress(Exception):
            data = json.loads(html_list[1])
        clist = data.get("data", []) if isinstance(data, dict) else []

        chapters: list[ChapterInfoDict] = []
        for chap in clist:
            ordernum = str(chap.get("ordernum", "")).strip()
            if not ordernum:
                continue
            title = self._norm_space(chap.get("title", "") or "") or "未命名章节"
            url = f"/read/{book_id}/p{ordernum}.html" if book_id else ""
            chapters.append(
                {
                    "url": url,
                    "title": title,
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
        if not html_list:
            return None
        tree = html.fromstring(html_list[0])

        title = self._first_str(tree.xpath("//div[@class='page-d-top']/h1/text()"))
        if not title:
            title = self._first_str(
                tree.xpath("//article[contains(@class,'page-content')]//h3/text()")
            )
        title = self._norm_space(title)

        # paragraphs within the reading section; skip ad containers
        ps = tree.xpath(
            "//article[contains(@class,'page-content')]//section//p[not(contains(@class,'abg'))]"
        )

        paragraphs: list[str] = []
        for p in ps:
            raw = p.text_content()
            txt = self._norm_space(raw)
            if not txt or self._is_ad_line(txt):
                continue
            paragraphs.append(txt)

        if not paragraphs:
            return None

        # Replace FIRST line with .replace(title, "")
        first = paragraphs[0].replace(title, "")
        first = first.replace(title.replace(" ", ""), "").strip()
        if first:
            paragraphs[0] = first
        else:
            paragraphs.pop(0)

        if paragraphs:
            last = paragraphs[-1]
            if "本章完" in last:
                paragraphs.pop()

        content = "\n".join(paragraphs)
        if not content.strip():
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }

    @classmethod
    def _meta(cls, tree: html.HtmlElement, prop: str) -> str:
        return cls._first_str(tree.xpath(f"//meta[@property='{prop}']/@content"))
