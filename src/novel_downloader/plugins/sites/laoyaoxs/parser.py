#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.laoyaoxs.parser
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
class LaoyaoxsParser(BaseParser):
    """
    Parser for 老幺小说网 book-info pages.
    """

    site_name: str = "laoyaoxs"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if len(html_list) < 2:
            return None

        info_tree = html.fromstring(html_list[0])
        catalog_tree = html.fromstring(html_list[1])

        # Metadata extraction
        book_name = self._first_str(
            info_tree.xpath('//meta[@property="og:novel:book_name"]/@content')
        ) or self._first_str(
            info_tree.xpath('//div[contains(@class,"detail")]//h1/text()')
        )

        author = self._first_str(
            info_tree.xpath('//meta[@property="og:novel:author"]/@content')
        ) or self._first_str(
            info_tree.xpath('//div[contains(@class,"detail")]//p//a[1]/text()')
        )

        category = self._first_str(
            info_tree.xpath('//meta[@property="og:novel:category"]/@content')
        )

        cover_url = self._first_str(
            info_tree.xpath('//meta[@property="og:image"]/@content')
        ) or self._first_str(
            info_tree.xpath('//a[contains(@class,"bookimg")]//img/@src')
        )
        if cover_url.startswith("//"):
            cover_url = "https:" + cover_url

        update_time = self._first_str(
            info_tree.xpath('//meta[@property="og:novel:update_time"]/@content'),
            replaces=[("\xa0", " "), ("\u3000", " ")],
        )

        summary = self._join_strs(
            info_tree.xpath('//p[contains(@class,"intro")]//text()')
        )

        # Chapter list extraction
        chapters: list[ChapterInfoDict] = [
            {
                "title": (a.get("title") or (a.text or "")).strip(),
                "url": (a.get("href") or "").strip(),
                "chapterId": (a.get("href") or "").split(".", 1)[0],
            }
            for a in catalog_tree.xpath(
                '//div[contains(@class,"read")]//dl[@id="newlist"]//dd//a[1]'
            )
        ]
        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "tags": [category] if category else [],
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

        title_text = self._first_str(
            tree.xpath('//div[@id="chapter-name"]//h2/text()')
        ) or self._first_str(tree.xpath("//h2/text()"))

        containers = tree.xpath('//div[contains(@class,"main_content") or @id="txt"]')
        fragments: list[tuple[int, str]] = []

        if containers:
            container = containers[0]
            for dd in container.xpath(".//dd[@data-id]"):
                data_id_raw = (dd.get("data-id") or "").strip()
                try:
                    order_idx = int(data_id_raw)
                except ValueError:
                    continue

                dd_text = self._join_strs(dd.xpath(".//p//text()"))
                if dd_text.strip():
                    fragments.append((order_idx, dd_text))

        if not fragments:
            return None

        fragments.sort(key=lambda x: x[0])
        content_text = "\n".join(text for _, text in fragments).strip()

        if not content_text.strip():
            return None

        return {
            "id": chapter_id,
            "title": title_text,
            "content": content_text,
            "extra": {"site": self.site_name},
        }
