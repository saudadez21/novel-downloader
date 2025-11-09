#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.syosetu.parser
---------------------------------------------
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
class SyosetuParser(BaseParser):
    """
    Parser for 小説家になろう book pages.
    """

    site_name: str = "syosetu"
    BASE_URL = "https://ncode.syosetu.com"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        book_name = self._first_str(
            tree.xpath('//h1[contains(@class,"p-novel__title")]/text()')
        )
        author = self._first_str(
            tree.xpath('//div[contains(@class,"p-novel__author")]//a/text()')
        )
        if not author:
            author = self._first_str(
                tree.xpath('//div[contains(@class,"p-novel__author")]/text()'),
                replaces=[("作者：", "")],
            )
        cover_url = self._first_str(tree.xpath('//meta[@property="og:image"]/@content'))
        if cover_url and not cover_url.startswith("http"):
            cover_url = "https:" + cover_url

        summary = self._join_strs(tree.xpath('//div[@id="novel_ex"]//text()'))

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

        for html_page in html_list:
            t = html.fromstring(html_page)

            for elem in t.xpath('//div[@class="p-eplist"]/*'):
                if "p-eplist__chapter-title" in elem.get("class", ""):
                    flush_volume()
                    vol_name = elem.text_content().strip()
                    continue

                if "p-eplist__sublist" in elem.get("class", ""):
                    a = elem.xpath('.//a[contains(@class,"p-eplist__subtitle")]')
                    if not a:
                        continue
                    href = (a[0].get("href") or "").strip()
                    title = (a[0].text_content() or "").strip()
                    if not href or not title:
                        continue

                    chap_id = href.strip("/").split("/")[-1]
                    vol_chaps.append(
                        {
                            "title": title,
                            "url": href,
                            "chapterId": chap_id,
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
            tree.xpath('//h1[contains(@class,"p-novel__title")]/text()')
        )

        # Extract paragraphs of content
        paragraphs: list[str] = []
        image_positions: dict[int, list[dict[str, Any]]] = {}
        image_idx = 0

        for div in tree.xpath(
            '//div[@class="p-novel__body"]/div[contains(@class,"p-novel__text")]'
        ):
            for p in div.xpath("./p"):
                # --- collect images ---
                for src in p.xpath(".//img/@src"):
                    src = src.strip()
                    if not src:
                        continue
                    if not src.startswith("http"):
                        src = "https:" + src
                    image_positions.setdefault(image_idx, []).append(
                        {
                            "type": "url",
                            "data": src,
                        }
                    )

                # --- collect text ---
                if text := p.text_content().strip():
                    paragraphs.append(text)
                    image_idx += 1

        if not (paragraphs or image_positions):
            return None

        content = "\n".join(paragraphs)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {
                "site": self.site_name,
                "image_positions": image_positions,
            },
        }
