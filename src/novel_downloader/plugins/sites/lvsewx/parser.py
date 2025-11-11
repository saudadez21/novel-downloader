#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.lvsewx.parser
--------------------------------------------
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
class LvsewxParser(BaseParser):
    """
    Parser for 绿色小说网 book pages.
    """

    site_name: str = "lvsewx"
    BASE_URL = "https://www.lvsewx.cc"
    ADS: set[str] = {
        r"www\.lvscwx\.cc",
    }

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        book_name = self._first_str(
            tree.xpath('//meta[@property="og:novel:book_name"]/@content')
            or tree.xpath('//meta[@property="og:title"]/@content')
            or tree.xpath('//div[@class="info"]/h2/text()')
        )
        author = self._first_str(
            tree.xpath('//meta[@property="og:novel:author"]/@content')
            or tree.xpath('//div[@class="small"]/span[contains(text(),"作者")]/text()'),
            replaces=[("作者：", "")],
        )

        cover_url = self._first_str(
            tree.xpath('//meta[@property="og:image"]/@content')
            or tree.xpath('//div[@class="cover"]/img/@src')
        )
        if cover_url.startswith("//"):
            cover_url = "https:" + cover_url
        elif cover_url.startswith("/"):
            cover_url = self.BASE_URL + cover_url

        update_time = self._first_str(
            tree.xpath('//meta[@property="og:novel:update_time"]/@content')
            or tree.xpath(
                '//div[@class="small"]/span[contains(text(),"更新时间")]/text()'
            ),  # noqa: E501
            replaces=[("更新时间：", "")],
        )
        serial_status = self._first_str(
            tree.xpath('//meta[@property="og:novel:status"]/@content')
            or tree.xpath('//div[@class="small"]/span[contains(text(),"状态")]/text()'),
            replaces=[("状态：", "")],
        )

        summary = self._join_strs(
            tree.xpath('//div[@class="intro"]//text()'), replaces=[("简介：", "")]
        )
        summary = summary.rsplit("作者：", 1)[0].strip()

        category = self._first_str(
            tree.xpath('//meta[@property="og:novel:category"]/@content')
            or tree.xpath('//div[@class="small"]/span[contains(text(),"分类")]/text()'),
            replaces=[("分类：", "")],
        )
        tags = [category] if category else []

        # --- Volumes & Chapters ---
        chapters: list[ChapterInfoDict] = []
        start: bool = False
        for elem in tree.xpath('//div[@class="listmain"]/dl/*'):
            tag = (elem.tag or "").lower()
            if tag == "dt":
                start = "正文卷" in elem.text_content()
                continue
            if tag == "dd" and start:
                for a in elem.xpath(".//a"):
                    href = (a.get("href") or "").strip()
                    if not href:
                        continue  # skip invalid entries
                    title = (a.text or "").strip()
                    chapter_id = href.rsplit("/", 1)[-1].split(".", 1)[0]
                    chapters.append(
                        {"title": title, "url": href, "chapterId": chapter_id}
                    )

        if not chapters:
            chapters = [
                {
                    "title": (a.text or "").strip(),
                    "url": (a.get("href") or "").strip(),
                    "chapterId": (a.get("href") or "")
                    .rsplit("/", 1)[-1]
                    .split(".", 1)[0],
                }
                for a in tree.xpath('//div[@id="listmain"]//dd/a')
            ]

        if not chapters:
            return None

        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "serial_status": serial_status,
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
            tree.xpath('//div[@class="content"]/h1/text()') or tree.xpath("//h1/text()")
        )

        paragraphs: list[str] = []

        # Iterate through direct children of content div
        for content_div in tree.xpath('//div[@id="content"]'):
            first_text = (content_div.text or "").strip()
            if first_text and not self._is_ad_line(first_text):
                paragraphs.append(first_text)

            for elem in content_div:
                tag = (elem.tag or "").lower()

                if tag == "script":
                    tail = (elem.tail or "").strip()
                    if tail and not self._is_ad_line(tail):
                        paragraphs.append(tail)
                    continue

                if tag == "br":
                    tail = (elem.tail or "").strip()
                    if tail and not self._is_ad_line(tail):
                        paragraphs.append(tail)
                    continue

                text = elem.text_content().strip()
                if text and not self._is_ad_line(text):
                    paragraphs.append(text)

                tail = (elem.tail or "").strip()
                if tail and not self._is_ad_line(tail):
                    paragraphs.append(tail)

        if not paragraphs:
            return None

        content = "\n".join(paragraphs)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {
                "site": self.site_name,
            },
        }
