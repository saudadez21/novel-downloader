#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n71ge.parser
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
class N71geParser(BaseParser):
    """
    Parser for 新吾爱文学 book pages.
    """

    site_name: str = "n71ge"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None
        tree = html.fromstring(html_list[0])

        book_name = (
            self._first_str(tree.xpath("//meta[@name='og:novel:book_name']/@content"))
            or self._first_str(tree.xpath("//meta[@property='og:title']/@content"))
            or self._first_str(tree.xpath("//div[@class='introduce']//h1/text()"))
        )

        author = (
            self._first_str(tree.xpath("//meta[@name='og:novel:author']/@content"))
            or self._first_str(tree.xpath("//meta[@name='author']/@content"))
            or self._first_str(
                tree.xpath(
                    "//div[@class='introduce']//p[@class='bq']//span[contains(., '作者')]/a/text()"  # noqa: E501
                )
            )
        )

        cover_url = self._first_str(
            tree.xpath("//meta[@property='og:image']/@content")
        ) or self._first_str(tree.xpath("//div[contains(@class,'pic')]//img/@src"))

        serial_status = self._first_str(
            tree.xpath("//meta[@property='og:novel:status']/@content")
        ) or self._first_str(
            tree.xpath("//div[@class='introduce']//span[contains(., '状态')]/text()"),
            replaces=[("状态：", "")],
        )

        update_time = self._first_str(
            tree.xpath("//meta[@name='og:novel:update_time']/@content")
        ) or self._first_str(
            tree.xpath("//div[@class='introduce']//span[contains(., '更新')]/text()"),
            replaces=[("更新：", "")],
        )

        category = self._first_str(
            tree.xpath("//meta[@property='og:novel:category']/@content")
        )
        tags = [category] if category else []

        summary = self._first_str(
            tree.xpath("//meta[@property='og:description']/@content")
        ) or self._norm_space(
            tree.xpath("string(//div[@class='introduce']//p[@class='jj'])")
        )

        chapters: list[ChapterInfoDict] = [
            {
                "title": (a.text or "").strip(),
                "url": (a.get("href") or "").strip(),
                "chapterId": (a.get("href") or "").rsplit("/", 1)[-1].split(".", 1)[0],
            }
            for a in tree.xpath("//div[contains(@class,'ml_list')]//ul/li/a")
        ]
        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "serial_status": serial_status,
            "update_time": update_time,
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

        title_text: str = ""
        contents: list[str] = []
        for curr_html in html_list:
            tree = html.fromstring(curr_html)

            if not title_text:
                title_text = self._first_str(
                    tree.xpath(
                        "//div[@id='nr_content']//div[@class='nr_title']/h3/text()"
                    )
                )

            for p in tree.xpath(
                "//div[@id='nr_content']//div[@class='novelcontent']//p"
            ):
                for elem in p.iter():
                    if elem.text:
                        contents.append(elem.text.strip())
                    if elem.tail:
                        contents.append(elem.tail.strip())

            if not contents:
                continue
            if contents[-1].startswith("本章未完") or contents[-1].startswith(
                "本章已完"
            ):  # noqa: E501
                contents.pop()

        return {
            "id": chapter_id,
            "title": title_text,
            "content": "\n".join(contents),
            "extra": {"site": self.site_name},
        }
