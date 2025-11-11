#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n69shuba.parser
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
class N69shubaParser(BaseParser):
    """
    Parser for 69书吧 book pages.
    """

    site_name: str = "n69shuba"

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
            info_tree.xpath('//div[@class="booknav2"]/h1/a/text()')
        )
        author = self._first_str(
            info_tree.xpath(
                '//div[@class="booknav2"]/p[contains(text(),"作者")]/a/text()'
            )
        )
        cover_url = self._first_str(
            info_tree.xpath('//div[@class="bookimg2"]/img/@src')
        )

        # "123.45万字 | 连载"
        stats = self._first_str(
            info_tree.xpath('//div[@class="booknav2"]/p[contains(text(),"字")]/text()')
        ).split("|")
        word_count = stats[0].strip() if stats else ""
        serial_status = stats[1].strip() if len(stats) > 1 else ""

        update_time = self._first_str(
            info_tree.xpath('//div[@class="booknav2"]/p[contains(text(),"更新")]/text()'),
            replaces=[("更新：", "")],
        )

        summary = self._join_strs(info_tree.xpath('//div[@class="navtxt"]//p//text()'))

        # --- Chapter volumes & listings ---
        chapters: list[ChapterInfoDict] = []
        for a in catalog_tree.xpath('//div[@id="catalog"]//ul/li/a'):
            url = a.get("href", "").strip()
            if not url:
                continue
            chap_id = url.strip("/").rsplit("/", 1)[-1]
            title = self._first_str(a.xpath(".//text()"))
            chapters.append(
                {
                    "title": title,
                    "url": url,
                    "chapterId": chap_id,
                }
            )

        if not chapters:
            return None

        # catalog is newest-first, so reverse
        chapters.reverse()

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

        tree = html.fromstring(html_list[0])

        title = ""
        paragraphs: list[str] = []

        # Iterate through direct children of content div
        for elem in tree.xpath('//div[contains(@class,"txtnav")]/*'):
            tag = (elem.tag or "").lower()
            cls = (elem.get("class") or "").lower()
            eid = elem.get("id", "").lower()

            # --- title ---
            if tag == "h1" and not title:
                title = elem.text_content().strip()
                if tail := (elem.tail or "").strip():
                    paragraphs.append(tail)
                continue

            # --- skip metadata/ads ---
            if "txtinfo" in cls:
                if tail := (elem.tail or "").strip():
                    paragraphs.append(tail)
                continue
            if "bottom-ad" in cls:
                if tail := (elem.tail or "").strip():
                    paragraphs.append(tail)
                continue
            if "txtright" in eid:
                if tail := (elem.tail or "").strip():
                    paragraphs.append(tail)
                continue

            # --- handle line breaks ---
            if tag == "br":
                if tail := (elem.tail or "").strip():
                    paragraphs.append(tail)
                continue

            # --- normal text elements ---
            if text := elem.text_content().strip():
                paragraphs.append(text)
            if tail := (elem.tail or "").strip():
                paragraphs.append(tail)

        if not paragraphs:
            return None
        if paragraphs[0].strip() == title.strip():
            paragraphs.pop(0)

        if not paragraphs:
            return None
        last = paragraphs[-1].rstrip()
        if last.endswith("(本章完)"):
            last = last[: -len("(本章完)")].rstrip()
            if last:
                paragraphs[-1] = last
            else:
                paragraphs.pop()

        if not paragraphs:
            return None

        content = "\n".join(paragraphs)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
