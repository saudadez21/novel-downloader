#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ruochu.parser
--------------------------------------------
"""

import json
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
class RuochuParser(BaseParser):
    """
    Parser for 若初文学网 book pages.
    """

    site_name: str = "ruochu"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if len(html_list) < 2:
            return None

        info_tree = html.fromstring(html_list[0])
        catalog_tree = html.fromstring(html_list[1])

        # --- base info ---
        book_name = self._first_str(
            info_tree.xpath(
                '//div[contains(@class,"pattern-cover-detail")]//h1//span/text()'
            )
        )
        author = self._first_str(
            info_tree.xpath(
                '//div[contains(@class,"notify")]//text()[contains(.,"作者")]'
            )
        )
        cover_url = self._first_str(
            info_tree.xpath('//div[@class="pic"]//img[@class="book-cover"]/@src')
        )
        word_count = self._first_str(
            info_tree.xpath('//span[contains(@class,"words")]/text()')
        )
        serial_status = (
            "连载中"
            if info_tree.xpath('//i[contains(@class,"is-serialize")]')
            else "完结"  # noqa: E501
        )
        update_time = self._first_str(info_tree.xpath('//span[@class="time"]/text()'))

        summary = self._join_strs(
            info_tree.xpath(
                '//div[contains(@class,"summary")]//pre[@class="note"]/text()'
            )
        )

        # --- Chapter volumes & listings ---
        chapters: list[ChapterInfoDict] = []
        for a in catalog_tree.xpath('//div[contains(@class,"chapter-list")]//ul/li/a'):
            url = a.get("href", "").strip()
            if not url:
                continue
            title = a.text_content().strip()
            chap_id = url.strip("/").rsplit("/", 1)[-1]
            accessible = "isvip" not in (a.get("class") or "")
            chapters.append(
                {
                    "title": title,
                    "url": url,
                    "chapterId": chap_id,
                    "accessible": accessible,
                }
            )

        if not chapters:
            return None

        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "serial_status": serial_status,
            "word_count": word_count,
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

        text = html_list[0]
        if '"chapter"' not in text:
            return None
        if "(" in text and ")" in text:
            json_str = text.split("(", 1)[-1].rsplit(")", 1)[0].strip()
        else:
            return None

        data = json.loads(json_str)
        chapter = data.get("chapter")
        if not chapter:
            return None
        html_content = chapter.get("htmlContent")
        if not html_content:
            return None

        title = chapter.get("title") or ""
        tree = html.fromstring(html_content)

        paragraphs: list[str] = [
            text for p in tree.xpath("//p") if (text := p.text_content().strip())
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
