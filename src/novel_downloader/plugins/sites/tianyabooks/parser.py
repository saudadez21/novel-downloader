#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.tianyabooks.parser
-------------------------------------------------
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
class TianyabooksParser(BaseParser):
    """
    Parser for 天涯书库 book pages.
    """

    site_name: str = "tianyabooks"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        book_name = (
            self._first_str(tree.xpath('//div[@class="catalog"]/h1/text()'))
            or self._first_str(tree.xpath('//div[@class="book"]/h1/text()'))
            or "未知书名"
        )

        author = (
            self._first_str(tree.xpath('//div[@class="catalog"]/h2//a/text()'))
            or self._first_str(tree.xpath('//div[@class="book"]/h2//a/text()'))
            or self._first_str(
                tree.xpath('//div[@class="catalog"]/div[@class="info"]/text()')
                + tree.xpath('//div[@class="book"]/h2/text()'),
                replaces=[("作者：", "")],
            )
            or "未知作者"
        )
        summary = (
            self._join_strs(
                tree.xpath('//div[@class="description"]//p/text()')
                + tree.xpath('//div[@class="summary"]//p/text()')
            )
            or "无简介"
        )

        # --- Volume extraction attempts ---
        volume_xpaths = [
            "//dl/*",  # <dl><dt>/<dd>
            '//div[@class="mulu-title" or @class="mulu-list"]',  # <div class="mulu-*">
            '//div[@class="idx-title" or @class="idx-list"]',  # <div class="idx-*">
        ]

        volumes: list[VolumeInfoDict] = []
        for xp in volume_xpaths:
            volumes = self._parse_volume_nodes(tree, xp)
            if volumes:
                break

        if not volumes:
            return None

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": "",
            "update_time": "",
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
        title_xpaths = [
            '//div[@class="article"]/h2/text()',
            '//div[@id="main"]/h1/text()',
            '//div[@class="book"]/h1/text()',
            '//div[@class="content" or @class="content book-content"]/h1/text()',
        ]
        title = ""
        for xp in title_xpaths:
            title = self._first_str(tree.xpath(xp))
            if title:
                break

        paragraph_xpaths = [
            '//div[@class="article"]//p//text()',
            '//div[@id="main"]//p//text()',
            '//div[@id="neirong"]//p//text()',
            '//div[@class="book"]//p//text()',
            '//div[@class="content" or @class="content book-content"]//p//text()',
        ]

        paragraphs: list[str] = []
        for xp in paragraph_xpaths:
            paragraphs = [s.strip() for s in tree.xpath(xp) if s.strip()]
            if paragraphs:
                break

        if not paragraphs:
            return None

        content = "\n".join(paragraphs)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }

    def _parse_volume_nodes(
        self, tree: html.HtmlElement, xpath_expr: str
    ) -> list[VolumeInfoDict]:
        """Shared logic to build volumes/chapters list with title/list pairing."""
        volumes: list[VolumeInfoDict] = []
        vol_idx = 1
        vol_name: str | None = None
        vol_chaps: list[ChapterInfoDict] = []

        for elem in tree.xpath(xpath_expr):
            tag = (elem.tag or "").lower()
            cls = elem.get("class", "")

            # --- Title node ---
            if tag == "dt" or "title" in cls:
                # If there's an unfinished volume, flush it first
                if vol_chaps:
                    volumes.append(
                        {
                            "volume_name": vol_name or f"未命名卷 {vol_idx}",
                            "chapters": vol_chaps,
                        }
                    )
                    vol_idx += 1
                    vol_chaps = []

                # Update volume name
                vol_name = elem.text_content().strip()

            # --- List node (chapter links) ---
            elif tag == "dd" or "list" in cls:
                for a in elem.xpath(".//a"):
                    href = a.get("href", "").strip()
                    if not href:
                        continue
                    title = a.text_content().strip()
                    chap_id = href.rsplit("/", 1)[-1].split(".", 1)[0]
                    vol_chaps.append(
                        {"title": title, "url": href, "chapterId": chap_id}
                    )

        # Flush last volume
        if vol_chaps:
            volumes.append(
                {
                    "volume_name": vol_name or f"未命名卷 {vol_idx}",
                    "chapters": vol_chaps,
                }
            )

        return volumes
