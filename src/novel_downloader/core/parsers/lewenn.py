#!/usr/bin/env python3
"""
novel_downloader.core.parsers.lewenn
------------------------------------

"""

from typing import Any

from lxml import html

from novel_downloader.core.parsers.base import BaseParser
from novel_downloader.core.parsers.registry import register_parser
from novel_downloader.models import (
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    VolumeInfoDict,
)


@register_parser(
    site_keys=["lewenn", "lewen"],
)
class LewennParser(BaseParser):
    """
    Parser for 乐文小说网 book pages.
    """

    BASE_URL = "https://www.lewenn.net"

    ADS: set[str] = {
        "app2",
        "read2",
        "chaptererror",
        "记住乐文小说网",
        "lewenn.net",
    }

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        # --- Metadata ---
        book_name = self._first_str(tree.xpath('//div[@id="info"]/h1/text()'))
        author = self._first_str(
            tree.xpath('//div[@id="info"]/p[1]/text()'),
            replaces=[(chr(0xA0), ""), ("作者：", "")],
        )
        serial_status = self._first_str(
            tree.xpath('//div[@id="info"]/p[2]/text()'),
            replaces=[(chr(0xA0), ""), ("状态：", "")],
        )
        update_time = self._first_str(
            tree.xpath('//div[@id="info"]/p[3]/text()'),
            replaces=[("最后更新：", "")],
        )

        cover_src = self._first_str(tree.xpath('//div[@id="sidebar"]//img/@src'))
        cover_url = (
            cover_src if cover_src.startswith("http") else f"{self.BASE_URL}{cover_src}"
        )

        summary_lines = tree.xpath('//div[@id="intro"]/p//text()')
        summary = "\n".join(line.strip() for line in summary_lines).strip()

        # --- Volumes & Chapters ---
        chapters: list[ChapterInfoDict] = []
        for dt in tree.xpath('//div[@class="listmain"]/dl/dt'):
            title_text = dt.text_content().strip()
            if "正文" in title_text:
                # collect its <dd> siblings
                sib = dt.getnext()
                while sib is not None and sib.tag == "dd":
                    a = sib.xpath(".//a")[0]
                    chap_title = a.text_content().strip()
                    href = a.get("href")
                    url = href if href.startswith("http") else f"{self.BASE_URL}{href}"
                    chap_id = url.rstrip(".html").split("/")[-1]
                    chapters.append(
                        {"title": chap_title, "url": url, "chapterId": chap_id}
                    )
                    sib = sib.getnext()
                break

        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "serial_status": serial_status,
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

        title = self._first_str(tree.xpath('//div[@class="content"]/h1/text()'))

        nodes = tree.xpath('//div[@id="content" and contains(@class,"showtxt")]')
        if not nodes:
            return None
        content_div = nodes[0]

        raw_lines = [ln.strip() for ln in content_div.xpath(".//text()")]

        lines: list[str] = []
        for ln in raw_lines:
            if not ln or self._is_ad_line(ln):
                continue
            # if ln.startswith("(") and ln.endswith(")"):
            #     continue
            lines.append(ln.replace(chr(0xA0), ""))

        content = "\n".join(lines)
        if not content.strip():
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": "lewenn"},
        }
