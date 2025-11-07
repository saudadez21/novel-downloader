#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.uaa.parser
-----------------------------------------
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
class UaaParser(BaseParser):
    """
    Parser for 有爱爱 book pages.
    """

    site_name: str = "uaa"
    BASE_URL = "https://www.uaa.com"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        # Book metadata
        book_name = self._first_str(tree.xpath('//div[@class="info_box"]/h1/text()'))
        author = self._first_str(
            tree.xpath('//div[@class="item"][contains(text(),"作者")]/a/text()')
        )
        cover_url = self._first_str(tree.xpath('//img[@class="cover"]/@src'))
        serial_status = self._first_str(
            tree.xpath('//span[contains(@class,"update_state")]/text()'),
            [("状态：", "")],
        )
        word_count = self._first_str(
            tree.xpath(
                '//li/img[contains(@src,"word_count")]/following-sibling::text()'
            )
        )

        # Tags
        category_tags = {
            s
            for t in tree.xpath('//div[@class="item"][contains(.,"题材")]/a/text()')
            if (s := t.strip())
        }
        user_tags = {
            s
            for t in tree.xpath('//ul[@class="tag_box"]/li/a/text()')
            if (s := t.strip().lstrip("#").strip())
        }
        tags = list(category_tags | user_tags)

        summary = self._join_strs(
            tree.xpath('//div[@class="brief_box"]//div[contains(@class,"txt")]/text()'),
            [("小说简介：", "")],
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

        for li in tree.xpath('//ul[@class="catalog_ul"]/li'):
            li_class = li.get("class", "")

            if "volume" in li_class:
                flush_volume()
                vol_name = self._first_str(li.xpath("./span/text()"))

                for cli in li.xpath(
                    './/ul[contains(@class,"children")]/li[contains(@class,"child")]'
                ):
                    a = cli.xpath(".//a")
                    if not a:
                        continue
                    href = (a[0].get("href") or "").strip()
                    if not href:
                        continue
                    title = a[0].text_content().strip()
                    chapter_id = href.split("id=")[-1]
                    vol_chaps.append(
                        {
                            "title": title,
                            "url": href,
                            "chapterId": chapter_id,
                        }
                    )

                flush_volume()
                continue

            if "menu" in li_class:
                a = li.xpath(".//a")
                if not a:
                    continue
                href = (a[0].get("href") or "").strip()
                if not href:
                    continue
                title = a[0].text_content().strip()
                chapter_id = href.split("id=")[-1]
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
            "update_time": "",
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
        if not html_list:
            return None
        tree = html.fromstring(html_list[0])

        title = self._first_str(
            tree.xpath('//div[contains(@class,"title_box")]//h2//text()')
        )

        paragraphs: list[str] = [
            text
            for p in tree.xpath(
                '//div[@class="article"]//div[contains(@class,"line")]//text()[not(ancestor::span[contains(@class,"comment_icon")])]'
            )
            if (text := p.strip())
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
