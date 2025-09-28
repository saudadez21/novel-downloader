#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.kunnu.parser
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
class KunnuParser(BaseParser):
    """
    Parser for 鲲弩小说 book pages.
    """

    site_name: str = "kunnu"
    ADS = {
        r"鲲\W*弩\W*小\W*说",
    }

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        # ---- Metadata ----
        book_intro = tree.xpath('//div[contains(@class,"book-intro")]')[0]
        book_describe = book_intro.xpath('.//div[contains(@class,"book-describe")]')[0]

        cover_url = self._first_str(
            book_intro.xpath('.//div[@class="book-img"]//img/@src')
        )
        book_name = self._first_str(book_describe.xpath("./h1/text()"))

        author = self._first_str(
            book_describe.xpath('./p[contains(.,"作者")]/text()'),
            replaces=[("作者：", "")],
        )

        category = self._first_str(
            book_describe.xpath('./p[contains(.,"类型")]/text()'),
            replaces=[("类型：", "")],
        )

        serial_status = self._first_str(
            book_describe.xpath('./p[contains(.,"状态")]/text()'),
            replaces=[("状态：", "")],
        )

        update_time = self._first_str(
            book_describe.xpath('./p[contains(.,"最近更新")]/text()'),
            replaces=[("最近更新：", "")],
        )

        paras = []
        for p in tree.xpath('//div[@class="describe-html"][1]//p'):
            txt = "".join(p.xpath(".//text()")).strip()
            if txt:
                paras.append(txt)
        summary = "\n".join(paras)

        # --- Chapter volumes & listings ---
        volumes: list[VolumeInfoDict] = []
        current_volume_name: str | None = None
        current_chapters: list[ChapterInfoDict] = []

        def flush_volume() -> None:
            nonlocal current_volume_name, current_chapters
            if not current_chapters:
                return
            vol_name = current_volume_name if current_volume_name else "正文"
            volumes.append({"volume_name": vol_name, "chapters": current_chapters})
            current_volume_name = None
            current_chapters = []

        for node in tree.xpath(
            '//div[@id="content-list"]/div[contains(@class,"title") or contains(@class,"book-list")]'  # noqa: E501
        ):
            # A titled section
            if "title" in (node.get("class") or ""):
                # new volume -> flush previous
                flush_volume()
                current_volume_name = self._first_str(
                    node.xpath(".//h3//a/text()")
                ) or self._first_str(node.xpath(".//h3/text()"))
                continue

            # A chapter list block
            if "book-list" in (node.get("class") or ""):
                for a in node.xpath(".//ul//li/a"):
                    href = (a.get("href") or "").strip()
                    if not href:
                        continue
                    title = (a.get("title") or (a.text or "")).strip()
                    chapter_id = href.rsplit("/", 1)[-1].split(".")[0]
                    current_chapters.append(
                        {"title": title, "url": href, "chapterId": chapter_id}
                    )

        # Flush the last collected volume
        flush_volume()

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "serial_status": serial_status,
            "update_time": update_time,
            "summary": summary,
            "tags": [category] if category else [],
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
            tree.xpath('//h1[@id="nr_title" or contains(@class,"post-title")]/text()')
        )

        paragraphs: list[str] = []
        for p in tree.xpath('//div[@id="nr1"]//p'):
            txt = self._join_strs(p.xpath(".//text()"))
            if txt and not self._is_ad_line(txt):
                paragraphs.append(txt)

        content = "\n".join(paragraphs)
        if not content:
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
