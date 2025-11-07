#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.alphapolis.parser
------------------------------------------------
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
class AlphapolisParser(BaseParser):
    """
    Parser for アルファポリス book pages.
    """

    site_name: str = "alphapolis"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        main = tree.xpath(
            '//div[@class="cover novels section"]/div[@class="content-main"]'
        )
        info = tree.xpath('//div[@class="content-info gray-menu section"]')

        book_name = (
            self._first_str(main[0].xpath('.//h1[@class="title"]/text()'))
            if main
            else ""
        )
        author = (
            self._first_str(main[0].xpath('.//div[@class="author"]//a[1]/text()'))
            if main
            else ""
        )

        book_name = self._first_str(tree.xpath("//h1[contains(@class,'title')]/text()"))
        author = self._first_str(
            tree.xpath("//div[contains(@class,'author')]//a[1]/text()")
        )
        cover_url = (
            self._first_str(info[0].xpath('.//div[@class="cover"]//img/@src'))
            if info
            else ""
        )
        if not cover_url:
            cover_url = self._first_str(
                tree.xpath('//meta[@property="og:image"]/@content')
            )
        update_time = (
            self._first_str(
                info[0].xpath(
                    './/table[contains(@class,"detail")]//tr[th[text()="更新日時"]]/td/text()'
                )
            )
            if info
            else ""
        )

        tags = [
            s
            for t in (
                main[0].xpath(
                    './/div[@class="content-tags"]//span[@class="tag"]/a/text()'
                )
                if main
                else []
            )
            if t and (s := t.strip())
        ]

        summary = (
            self._join_strs(main[0].xpath('.//div[@class="abstract"]/text()'))
            if main
            else ""
        )
        if not summary:
            summary = self._first_str(
                tree.xpath('//meta[@name="description"]/@content')
            )

        # --- Volumes & Chapters ---
        volumes: list[VolumeInfoDict] = []
        vol_idx: int = 1
        vol_name: str | None = None
        vol_chaps: list[ChapterInfoDict] = []

        def flush_volume() -> None:
            nonlocal vol_idx, vol_name, vol_chaps
            if not vol_chaps:
                return

            volumes.append(
                {
                    "volume_name": vol_name or f"未命名卷 {vol_idx}",
                    "chapters": vol_chaps,
                }
            )

            vol_name = None
            vol_chaps = []
            vol_idx += 1

        for elem in tree.xpath('//div[@class="episodes"]/*'):
            tag = (elem.tag or "").lower()
            if tag == "h3":
                flush_volume()
                vol_name = elem.text_content().strip()
                continue

            if tag == "div" and "episode" in (elem.get("class") or ""):
                a = elem.xpath(".//a")[0]
                url = a.get("href", "").strip()
                chapter_id = url.rsplit("/", 1)[-1]
                title = a.xpath('string(.//span[@class="title"])').strip()
                vol_chaps.append(
                    {
                        "title": title,
                        "url": url,
                        "chapterId": chapter_id,
                    }
                )

        flush_volume()

        if not volumes:
            return None

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

        title = self._first_str(
            tree.xpath("//h2[contains(@class,'episode-title')]/text()")
        )

        paragraphs = [
            s for p in tree.xpath('//div[@id="novelBody"]//text()') if (s := p.strip())
        ]

        if not paragraphs:
            return None

        content = "\n".join(paragraphs)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
