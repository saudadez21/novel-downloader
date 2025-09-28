#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.lewenn.parser
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
class LewennParser(BaseParser):
    """
    Parser for 乐文小说网 book pages.
    """

    site_name: str = "lewenn"
    BASE_URL = "https://www.lewenn.net"
    ADS = {
        "记住乐文小说网",
        r"lewenn\.net",
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

        summary = self._join_strs(tree.xpath('//div[@id="intro"]/p//text()'))

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

        # collect all visible text inside #content, skipping scripts/styles
        raw_texts = tree.xpath(
            '//div[@id="content"]//text()[not(ancestor::script) and not(ancestor::style)]'  # noqa: E501
        )

        lines: list[str] = []
        for ln in raw_texts:
            # normalize spaces: \xa0 (nbsp) and \u3000 (ideographic space)
            s = ln.replace("\xa0", "").replace("\u3000", "").strip()
            if not s or self._is_ad_line(s):
                continue
            lines.append(s)

        content = "\n".join(lines)
        if not content.strip():
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
