#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.guidaye.parser
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
class GuidayeParser(BaseParser):
    """
    Parser for 名著阅读 book pages.
    """

    site_name: str = "guidaye"
    BASE_URL = "https://b.guidaye.com"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        # Book metadata
        book_name = self._first_str(tree.xpath('//h1[@class="page-title"]/a/text()'))
        author = self._first_str(
            tree.xpath('//div[@id="category-description-author"]/a/text()')
        )
        cover_url = self.BASE_URL + self._first_str(
            tree.xpath('//div[@id="category-description-image"]//img/@src')
        )

        # Summary paragraphs
        summary = (
            tree.xpath('string(//div[@id="category-description-text"])')
            .replace("内容简介：", "", 1)
            .strip()
        )

        # Chapter volumes & listings
        volumes: list[VolumeInfoDict] = []
        curr_vol: VolumeInfoDict = {"volume_name": "未命名卷", "chapters": []}

        items = tree.xpath('//div[@class="entry-content"]/ul/*')
        for elem in items:
            if elem.tag.lower() == "h3":
                # Flush previous volume
                if curr_vol["chapters"]:
                    volumes.append(curr_vol)
                curr_vol = {"volume_name": elem.text_content().strip(), "chapters": []}
            elif elem.tag.lower() == "li":
                link = elem.xpath(".//a")[0]
                href = link.get("href", "").strip()
                title = link.get("title", "").strip()
                cid_match = re.search(r"/(\d+)\.html$", href)
                chapter_id = cid_match.group(1) if cid_match else ""
                curr_vol["chapters"].append(
                    {"title": title, "url": href, "chapterId": chapter_id}
                )

        # Append last volume
        if curr_vol["chapters"]:
            volumes.append(curr_vol)

        # Timestamp of parsing
        share_text = tree.xpath('string(//div[@id="category-description-share"])')
        m = re.search(r"最近更新[：:]\s*([\d-]+)", share_text)
        update_time = m.group(1) if m else datetime.now().strftime("%Y-%m-%d")

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
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

        # Title from entry-title
        title = self._first_str(tree.xpath('//h1[@class="entry-title"]/text()'))

        # Extract paragraphs within entry-content
        full_text = tree.xpath('string(//div[@class="entry-content"])')
        full_text = full_text.replace("\u00A0", " ")

        # 3. Split into lines and clean up
        lines = [line.strip() for line in full_text.splitlines() if line.strip()]
        if not lines:
            return None

        content = "\n".join(lines)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
