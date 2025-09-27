#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.i25zw.parser
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
class I25zwParser(BaseParser):
    """
    Parser for 25中文网 book-info pages.
    """

    site_name: str = "i25zw"

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
        book_name = self._first_str(info_tree.xpath("//h1[@class='f21h']/text()"))
        author = self._first_str(info_tree.xpath("//h1[@class='f21h']/em/a/text()"))
        cover_url = self._first_str(info_tree.xpath("//div[@class='pic']/img/@src"))

        # Tags, status, word count, update time
        tag = self._first_str(
            info_tree.xpath("//b[contains(text(),'小说分类')]/parent::td/text()")
        )
        serial_status = self._first_str(
            info_tree.xpath("//b[contains(text(),'小说状态')]/parent::td/text()")
        )
        word_count = self._first_str(
            info_tree.xpath("//b[contains(text(),'全文字数')]/parent::td/text()")
        )
        raw_update = self._first_str(
            info_tree.xpath("//b[contains(text(),'更新时间')]/parent::td/text()")
        )
        update_time = raw_update.strip("()")

        # Summary from styled intro div
        full_intro = info_tree.xpath("string(//div[@class='intro'][@style])").strip()
        summary = full_intro.replace(f"关于{book_name}：", "", 1).strip()

        # Chapter list extraction
        dl = catalog_tree.xpath("//div[@id='list']/dl")[0]
        # Full-text section dd's
        dds = dl.xpath("./dd[preceding-sibling::dt[1][contains(., '正文')]]/a")
        if not dds:
            # Fallback to second <dt>'s following <dd>
            dds = dl.xpath("./dt[2]/following-sibling::dd/a")

        chapters: list[ChapterInfoDict] = []
        for a in dds:
            url = a.get("href", "").strip()
            title = a.text_content().strip()
            # '/311006/252845677.html' -> '252845677'
            chapter_id = url.split("/")[-1].split(".")[0]
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
            "word_count": word_count,
            "serial_status": serial_status,
            "tags": [tag] if tag else [],
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

        title_text = self._first_str(
            tree.xpath("//div[@class='zhangjieming']/h1/text()")
        )

        content_divs = tree.xpath("//div[@id='content']")
        if not content_divs:
            return None
        content_div = content_divs[0]

        # Only select direct <p> children to avoid nav links
        paragraphs = []
        for p in content_div.xpath("./p"):
            text = p.text_content().strip()
            if text:
                paragraphs.append(text)

        content_text = "\n".join(paragraphs)
        if not content_text.strip():
            return None

        return {
            "id": chapter_id,
            "title": title_text,
            "content": content_text,
            "extra": {"site": self.site_name},
        }
