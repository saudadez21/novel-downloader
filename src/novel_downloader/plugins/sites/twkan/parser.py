#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.twkan.parser
-------------------------------------------
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
class TwkanParser(BaseParser):
    """
    Parser for 台灣小說網 book pages.
    """

    site_name: str = "twkan"
    ADS = {
        r"twkan\.com",
        "台灣小說網",
    }

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
        for a in catalog_tree.xpath("//ul/li/a"):
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

        title = self._first_str(
            tree.xpath('//div[contains(@class,"txtnav")]//h1/text()')
        )
        paragraphs: list[str] = []

        # Iterate through direct children of content div
        for content_div in tree.xpath('//div[@id="txtcontent0"]'):
            first_text = (content_div.text or "").strip()
            if first_text and not self._is_ad_line(first_text):
                paragraphs.append(first_text)

            for elem in content_div:
                tag = (elem.tag or "").lower()
                cls = (elem.get("class") or "").lower()

                # --- skip ad and layout divs ---
                if any(k in cls for k in ("txtad", "txtcenter")):
                    tail = (elem.tail or "").strip()
                    if tail and not self._is_ad_line(tail):
                        paragraphs.append(tail)
                    continue

                # --- handle line breaks ---
                if tag == "br":
                    tail = (elem.tail or "").strip()
                    if tail and not self._is_ad_line(tail):
                        paragraphs.append(tail)
                    continue

                # --- normal text elements ---
                text = elem.text_content().strip()
                if text and not self._is_ad_line(text):
                    paragraphs.append(text)

                tail = (elem.tail or "").strip()
                if tail and not self._is_ad_line(tail):
                    paragraphs.append(tail)

        if not paragraphs:
            return None
        if paragraphs[0].strip() == title.strip():
            paragraphs.pop(0)

        if not paragraphs:
            return None

        content = "\n".join(paragraphs)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
