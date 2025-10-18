#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.hetushu.parser
---------------------------------------------

"""

import base64
import json
import logging
import re
from typing import Any

from lxml import html

from novel_downloader.plugins.base.parser import BaseParser
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import (
    BookInfoDict,
    ChapterDict,
    VolumeInfoDict,
)

logger = logging.getLogger(__name__)


@registrar.register_parser()
class HetushuParser(BaseParser):
    """
    Parser for 和图书 book pages.
    """

    site_name: str = "hetushu"
    BASE_URL = "https://www.hetushu.com"
    _RE_CHAPTER_SPLIT = re.compile(r"[A-Z]+%")

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if len(html_list) < 2:
            return None

        tree = html.fromstring(html_list[0])
        catalog_data: list[list[str]] = json.loads(html_list[1])

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

        for elem in catalog_data:
            if not elem:
                logger.warning(
                    "hetushu book_info: empty element in catalog data: %s", elem
                )
                continue

            match elem[0]:
                case "dt":
                    if curr_vol["chapters"]:
                        volumes.append(curr_vol)
                    curr_vol = {
                        "volume_name": elem[1].strip(),
                        "chapters": [],
                    }

                case "dd":
                    title = elem[1].strip()
                    chapter_id = elem[2] if len(elem) > 2 else ""
                    curr_vol["chapters"].append(
                        {"title": title, "url": "", "chapterId": chapter_id}
                    )

                case _:
                    logger.debug("hetushu book_info: unknown catalog tag: %s", elem[0])

        # Append the last volume if it has any chapters
        if curr_vol["chapters"]:
            volumes.append(curr_vol)

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": "",
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
        if len(html_list) < 2 or not html_list[1]:
            return None

        tree = html.fromstring(html_list[0])

        title = ""
        paragraphs: list[str] = []
        intro_paragraphs: list[str] = []
        start_collecting = False
        orders = self._parse_chapter_order(html_list[1])

        for elem in tree.xpath('//div[@id="content"]/*'):
            tag = elem.tag.lower()

            if tag == "h2" and "h2" in elem.get("class", "").split():
                # Found chapter title; begin collecting
                title = elem.text_content().strip()
                start_collecting = True
                continue

            if tag == "div":
                direct_text_nodes = [
                    stripped
                    for node in elem.xpath("text()")
                    if (stripped := node.strip())
                ]
                if not direct_text_nodes:
                    continue
                joined_text = "".join(direct_text_nodes)
                if start_collecting:
                    paragraphs.append(joined_text)
                else:
                    intro_paragraphs.append(joined_text)

        offset = 0
        reordered: list[str] = [""] * len(paragraphs)
        for i, order in enumerate(orders):
            target = order if order < 5 else order - offset
            reordered[target] = paragraphs[i]
            if order < 5:
                offset += 1

        if not reordered:
            return None
        content = "\n".join(reordered)
        intro_text = "\n".join(intro_paragraphs)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {
                "site": self.site_name,
                "vol_intro": intro_text if intro_text else None,
            },
        }

    @classmethod
    def _parse_chapter_order(cls, s: str) -> list[int]:
        decoded = base64.b64decode(s)
        decoded_str = decoded.decode(errors="ignore")
        parts = cls._RE_CHAPTER_SPLIT.split(decoded_str)
        return [int(i) for i in parts]
