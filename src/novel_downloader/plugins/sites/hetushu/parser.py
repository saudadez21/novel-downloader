#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.hetushu.parser
---------------------------------------------

"""

import re
from datetime import datetime
from typing import Any

from lxml import html

from novel_downloader.plugins.base.parser import BaseParser
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import (
    BookInfoDict,
    ChapterDict,
    VolumeInfoDict,
)


@registrar.register_parser()
class HetushuParser(BaseParser):
    """
    Parser for 和图书 book pages.
    """

    site_name: str = "hetushu"
    BASE_URL = "https://www.hetushu.com"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        # --- Metadata ---
        book_name = self._first_str(
            tree.xpath('//div[contains(@class,"book_info")]/h2/text()')
        )
        author = self._first_str(
            tree.xpath(
                '//div[contains(@class,"book_info")]/div[contains(.,"作者")]/a/text()'
            )
        )
        cover_url = self.BASE_URL + self._first_str(
            tree.xpath('//div[contains(@class,"book_info")]//img/@src')
        )

        cls_attr = self._first_str(
            tree.xpath('//div[contains(@class,"book_info")]/@class')
        )
        serial_status = "已完结" if "finish" in cls_attr else "连载中"

        tags = [
            a.strip()
            for a in tree.xpath('//dl[@class="tag"]//dd/a/text()')
            if a.strip()
        ]

        summary = self._join_strs(tree.xpath('//div[@class="intro"]/p/text()'))

        # --- Chapter volumes & listings ---
        volumes: list[VolumeInfoDict] = []
        curr_vol: VolumeInfoDict = {"volume_name": "未命名卷", "chapters": []}

        for elem in tree.xpath('//dl[@id="dir"]/*'):
            if elem.tag == "dt":
                # Start a new volume
                if curr_vol["chapters"]:
                    volumes.append(curr_vol)
                curr_vol = {
                    "volume_name": elem.text_content().strip(),
                    "chapters": [],
                }
            elif elem.tag == "dd":
                link = elem.xpath(".//a")[0]
                href = link.get("href", "").strip()
                title = link.get("title", "").strip()
                # Extract numeric chapterId from the URL
                m = re.search(r"/book/\d+/(?P<id>\d+)\.html", href)
                chapter_id = m.group("id") if m else ""
                curr_vol["chapters"].append(
                    {"title": title, "url": href, "chapterId": chapter_id}
                )

        # Append the last volume if it has any chapters
        if curr_vol["chapters"]:
            volumes.append(curr_vol)

        update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "serial_status": serial_status,
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
            tree.xpath('//div[@id="content"]//h2[@class="h2"]/text()')
        )

        paras = tree.xpath('//div[@id="content"]/div[not(@class)]/text()')
        paragraph_texts = [p.strip() for p in paras if p.strip()]

        content = "\n".join(paragraph_texts)
        if not content.strip():
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
