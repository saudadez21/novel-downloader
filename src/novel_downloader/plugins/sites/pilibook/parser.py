#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.pilibook.parser
----------------------------------------------
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
class PilibookParser(BaseParser):
    """
    Parser for 霹雳书屋 book pages.
    """

    site_name: str = "pilibook"
    BASE_URL = "https://www.pilibook.net"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if len(html_list) < 2:
            return None

        # Parse trees
        info_tree = html.fromstring(html_list[0])
        catalog_tree = html.fromstring(html_list[1])

        # --- Metadata ---
        book_name = self._first_str(
            info_tree.xpath('//h2[contains(@class,"works-intro-title")]//strong/text()')
        )
        author = self._first_str(
            info_tree.xpath('//a[contains(@class,"works-author-name")]/text()')
        )
        tags = info_tree.xpath('//a[contains(@class,"works-intro-tags-item")]/text()')

        serial_status = self._first_str(
            info_tree.xpath('//label[contains(@class,"works-intro-status")]/text()')
        )

        update_time = self._first_str(
            info_tree.xpath(
                '//ul[contains(@class,"works-chapter-log")]'
                '//li[span[contains(text(),"最新章")]]//span[contains(@class,"ui-text-gray6")]/text()'
            )
        )
        cover_url = self._first_str(
            info_tree.xpath('//div[contains(@class,"works-cover")]//img/@src')
        )
        if cover_url:
            cover_url = cover_url.strip()
            if cover_url.startswith("//"):
                cover_url = "https:" + cover_url
            elif cover_url.startswith("/"):
                cover_url = self.BASE_URL + cover_url

        summary = self._join_strs(
            info_tree.xpath('//p[contains(@class,"works-intro-short")]//text()')
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

        for elem in catalog_tree.xpath(
            '//div[contains(@class,"works-chapter-list-wr")]/*'
        ):
            tag = (elem.tag or "").lower()
            class_attr = elem.get("class") or ""

            # detect volume title
            if tag == "div" and "vloume" in class_attr:
                flush_volume()
                vol_name = elem.text_content().strip()
                continue

            # chapter list block
            if tag == "ol" and "chapter-page-new" in class_attr:
                for a in elem.xpath('.//a[contains(@href,"/read/")]'):
                    href = a.get("href", "").strip()
                    if not href:
                        continue
                    title = a.get("title") or a.text_content().strip()
                    chapter_id = href.rsplit("/", 1)[-1].split(".", 1)[0]
                    vol_chaps.append(
                        {
                            "title": title,
                            "url": href,
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
            "serial_status": serial_status,
            "update_time": update_time,
            "summary": summary,
            "volumes": volumes,
            "tags": tags,
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
            tree.xpath('//h3[contains(@class,"j_chapterName")]//span/text()')
        )
        paragraphs = [
            p.text_content().strip()
            for p in tree.xpath('//div[contains(@class,"j_readContent")]/p')
            if p.text_content().strip()
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
