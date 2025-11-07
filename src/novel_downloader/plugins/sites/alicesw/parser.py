#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.alicesw.parser
---------------------------------------------
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
class AliceswParser(BaseParser):
    """
    Parser for 爱丽丝书屋 book-info pages.
    """

    site_name: str = "alicesw"

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
            info_tree.xpath("//div[@id='detail-box']//h1/text()")
        )
        author = self._first_str(
            info_tree.xpath(
                "//div[@id='detail-box']//p/a[contains(@href,'author')]/text()"
            )
        )
        cover_url = self._first_str(
            info_tree.xpath(
                "//div[@class='pic']//img[contains(@class,'fengmian2')]/@src"
            )
        )

        tags = info_tree.xpath("//p[contains(text(),'标签')]/a/text()")
        tags = [t.strip() for t in tags if t.strip()]

        serial_status = self._first_str(
            info_tree.xpath("//div[@class='pic']/div[contains(text(),'状态')]/text()"),
            replaces=[("小说状态：", "")],
        )
        word_count = self._first_str(
            info_tree.xpath("//div[@class='pic']/div[contains(text(),'字数')]/text()"),
            replaces=[("小说字数：", "")],
        )
        update_time = self._first_str(
            info_tree.xpath(
                "//div[@id='detail-box']//div[contains(text(),'更新时间')]/text()"
            ),
            replaces=[("更新时间：", "")],
        )

        summary = self._join_strs(info_tree.xpath("//div[@class='intro']//text()"))

        chapters: list[ChapterInfoDict] = []
        for a in catalog_tree.xpath("//ul[@class='mulu_list']/li/a"):
            href = a.get("href", "").strip()
            if not href:
                continue

            title = a.text_content().strip()
            chapter_id = href.split(".")[0].split("book/")[-1].replace("/", "-")
            chapters.append(
                {
                    "title": title,
                    "url": href,
                    "chapterId": chapter_id,
                }
            )

        if not chapters:
            return None

        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "word_count": word_count,
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

        title = self._first_str(tree.xpath("//h3[@class='j_chapterName']/text()"))
        paragraphs = [
            text.strip()
            for p in tree.xpath("//div[contains(@class,'read-content')]//p")
            if (text := self._norm_space(p.text_content()))
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
