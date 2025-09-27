#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.aaatxt.parser
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
class AaatxtParser(BaseParser):
    """
    Parser for 3A电子书 book pages.
    """

    site_name: str = "aaatxt"
    ADS = {
        "按键盘上方向键",
        "未阅读完",
        "加入书签",
        "已便下次继续阅读",
        "更多原创手机电子书",
        "免费TXT小说下载",
    }

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        book_name = self._first_str(tree.xpath("//div[@class='xiazai']/h1/text()"))

        author = self._first_str(tree.xpath("//span[@id='author']/a/text()"))

        cover_url = self._first_str(
            tree.xpath("//div[@id='txtbook']//div[@class='fm']//img/@src")
        )

        update_time = self._first_str(
            tree.xpath("//div[@id='txtbook']//li[contains(text(), '上传日期')]/text()"),
            replaces=[("上传日期:", "")],
        )

        genre = self._first_str(
            tree.xpath("//div[@id='submenu']/h2/a[@class='lan']/text()")
        )
        tags = [genre] if genre else []

        summary = self._first_str(tree.xpath("//div[@id='jj']//p/text()"))

        download_url = self._first_str(
            tree.xpath("//div[@id='down']//li[@class='bd']//a/@href")
        )

        # Chapters from the book_list
        chapters: list[ChapterInfoDict] = []
        for a in tree.xpath("//div[@id='ml']//ol/li/a"):
            url = a.get("href", "").strip()
            chapter_id = url.split("/")[-1].replace(".html", "")
            title = a.text_content().strip()
            chapters.append(
                {
                    "title": title,
                    "url": url,
                    "chapterId": chapter_id,
                }
            )

        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "tags": tags,
            "summary": summary,
            "volumes": volumes,
            "extra": {"download_url": download_url},
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

        raw_title = self._first_str(tree.xpath("//div[@id='content']//h1/text()"))
        title = raw_title.split("-", 1)[-1].strip()

        texts = []
        for txt in tree.xpath("//div[@class='chapter']//text()"):
            line = txt.strip()
            # Skip empty/instruction/ad lines
            if not line or self._is_ad_line(txt):
                continue
            texts.append(line)

        content = "\n".join(texts)
        if not content:
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
