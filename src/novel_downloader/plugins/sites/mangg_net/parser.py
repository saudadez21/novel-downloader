#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.mangg_net.parser
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
class ManggNetParser(BaseParser):
    """
    Parser for 追书网 book pages.
    """

    site_name: str = "mangg_net"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        book_name = self._first_str(
            tree.xpath('//meta[@property="og:novel:book_name"]/@content')
        )
        author = self._first_str(
            tree.xpath('//meta[@property="og:novel:author"]/@content')
        )
        cover_url = self._first_str(tree.xpath('//meta[@property="og:image"]/@content'))
        if cover_url and not cover_url.startswith("http"):
            cover_url = "https:" + cover_url
        update_time = self._first_str(
            tree.xpath('//meta[@property="og:novel:update_time"]/@content')
        )
        serial_status = self._first_str(
            tree.xpath('//meta[@property="og:novel:status"]/@content')
        )
        category = self._first_str(
            tree.xpath('//meta[@property="og:novel:category"]/@content')
        )
        tags = [category] if category else []

        summary = self._first_str(
            tree.xpath('//meta[@property="og:description"]/@content'),
            replaces=[("\u00a0", ""), (" ", ""), ("<br>", "\n"), ("<br/>", "\n")],
        )
        if not summary:
            summary = self._join_strs(
                tree.xpath('//div[@id="intro_pc"]//text()'),
                replaces=[("\u00a0", " ")],
            )

        # --- Volumes & Chapters ---
        chapters: list[ChapterInfoDict] = [
            {
                "title": (a.text or "").strip(),
                "url": (href := (a.get("href") or "").strip()),
                "chapterId": href.split("/")[-1].split(".")[0],
            }
            for a in tree.xpath('//div[contains(@class,"book_list2")]//a[@href]')
        ]
        for curr_html in html_list[1:]:
            t = html.fromstring(curr_html)
            more: list[ChapterInfoDict] = [
                {
                    "title": (a.text or "").strip(),
                    "url": (href := (a.get("href") or "").strip()),
                    "chapterId": href.split("/")[-1].split(".")[0],
                }
                for a in t.xpath('//div[contains(@class,"book_list2")]//a[@href]')
            ]
            chapters.extend(more)

        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "serial_status": serial_status,
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

        title: str = ""
        paragraphs: list[str] = []

        for curr_html in html_list:
            tree = html.fromstring(curr_html)
            if not title:
                raw_title = self._first_str(tree.xpath("//h1/text()"))
                if raw_title:
                    if "《" in raw_title:
                        raw_title = raw_title.split("《", 1)[0]
                    title = raw_title.rstrip(" —-").strip()

            for article in tree.xpath("//article"):
                parts: list[str] = []

                for node in article.iter():
                    if node.tag in {
                        "script",
                        "style",
                        "title",
                        "meta",
                        "head",
                        "html",
                        "body",
                    }:
                        continue
                    text = node.text.strip() if node.text else ""
                    tail = node.tail.strip() if node.tail else ""
                    if text:
                        parts.append(text)
                    if tail:
                        parts.append(tail)

                # e.g. "第(1/3)页"
                if parts and parts[0].startswith("第(") and parts[0].endswith(")页"):
                    parts.pop(0)
                if parts and parts[-1].startswith("第(") and parts[-1].endswith(")页"):
                    parts.pop()
                paragraphs.append("\n".join(parts))

        content = "\n".join(paragraphs)
        if not content.strip():
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
