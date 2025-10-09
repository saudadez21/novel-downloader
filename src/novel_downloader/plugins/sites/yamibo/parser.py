#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.yamibo.parser
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
class YamiboParser(BaseParser):
    """
    Parser for 百合会 book pages.
    """

    site_name: str = "yamibo"
    BASE_URL = "https://www.yamibo.com"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        book_name = self._first_str(
            tree.xpath('//h3[contains(@class,"col-md-12")]/text()')
        )
        author = self._first_str(
            tree.xpath('//h5[contains(@class,"text-warning")]/text()')
        )
        cover_url = self.BASE_URL + self._first_str(
            tree.xpath('//img[contains(@class,"img-responsive")]/@src')
        )

        update_time = self._first_str(
            tree.xpath('//p[contains(text(),"更新时间：")]/text()'),
            replaces=[("更新时间：", "")],
        )
        serial_status = self._first_str(
            tree.xpath('//p[contains(text(),"作品状态：")]/text()'),
            replaces=[("作品状态：", "")],
        )
        book_type = self._first_str(
            tree.xpath('//p[contains(text(),"作品分类：")]/text()'),
            replaces=[("作品分类：", "")],
        )
        summary = self._first_str([tree.xpath('string(//div[@id="w0-collapse1"]/div)')])

        # volumes & chapters
        volumes: list[VolumeInfoDict] = []
        for volume_node in tree.xpath(
            '//div[contains(@class,"panel-info") and contains(@class,"panel-default")]'
        ):
            volume_name = (
                self._first_str(
                    volume_node.xpath(
                        './/div[contains(@class,"panel-heading")]//a/text()'
                    )
                )
                or "未命名卷"
            )
            chapters: list[ChapterInfoDict] = []
            for chap in volume_node.xpath(
                './/div[contains(@class,"panel-body")]//a[contains(@href,"view-chapter")]'
            ):
                title = self._first_str([chap.xpath("string()")])
                url = chap.get("href", "")
                chapter_id = url.split("id=")[-1]
                chapters.append({"title": title, "url": url, "chapterId": chapter_id})
            volumes.append({"volume_name": volume_name, "chapters": chapters})

        # fallback: flat chapter list
        if not volumes:
            chapters = []
            for chap in tree.xpath(
                '//div[@class="panel-body"]//a[contains(@href,"view-chapter")]'
            ):
                title = self._first_str([chap.xpath("string()")])
                url = chap.get("href", "")
                chapter_id = url.split("id=")[-1] if "id=" in url else ""
                chapters.append({"title": title, "url": url, "chapterId": chapter_id})
            volumes = [{"volume_name": "单卷", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "serial_status": serial_status,
            "tags": [book_type],
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

        paragraphs = [
            text
            for p in tree.xpath("//div[@id='w0-collapse1']//p//text()")
            if (text := self._norm_space(p))
        ]

        if not paragraphs:
            return None

        content = "\n".join(paragraphs)

        title = self._first_str(
            [tree.xpath("string(//section[contains(@class,'col-md-9')]//h3)")]
        )

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
