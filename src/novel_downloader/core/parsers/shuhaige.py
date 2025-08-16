#!/usr/bin/env python3
"""
novel_downloader.core.parsers.shuhaige
--------------------------------------

"""

import re
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
    site_keys=["shuhaige"],
)
class ShuhaigeParser(BaseParser):
    """Parser for 书海阁小说网 book pages."""

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        """
        Parse a book info page and extract metadata and chapter structure.

        :param html_list: Raw HTML of the book info page.
        :return: Parsed metadata and chapter structure as a dictionary.
        """
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])
        book_name = tree.xpath('string(//div[@id="info"]/h1)').strip()
        author_text = (
            tree.xpath('string(//div[@id="info"]/p[1])').replace("\xa0", "").strip()
        )
        m = re.search(r"作者[:：]?\s*(.+)", author_text)
        author = m.group(1).strip() if m else ""
        cover_list = tree.xpath('//div[@id="fmimg"]/img/@src')
        cover_url = cover_list[0].strip() if cover_list else ""
        ut_text = tree.xpath('string(//div[@id="info"]/p[3])').strip()
        update_time = ut_text.replace("最后更新：", "").strip()
        # summary = tree.xpath('string(//div[@id="intro"])').strip()
        summary = tree.xpath('string(//div[@id="intro"]/p[1])').strip()

        bt = tree.xpath('//div[@class="con_top"]/a[2]/text()')
        book_type = bt[0].strip() if bt else ""
        tags = [book_type] if book_type else []

        chapters: list[ChapterInfoDict] = []
        dt_list = tree.xpath('//div[@id="list"]/dl/dt[contains(., "正文")]')
        if dt_list:
            vol_dt = dt_list[0]
            for sib in vol_dt.itersiblings():
                if sib.tag == "dt":
                    break
                if sib.tag == "dd":
                    a = sib.xpath("./a")
                    if not a:
                        continue
                    a = a[0]
                    title = a.text.strip()
                    url = a.get("href", "").strip()
                    # extract "3899817" from "/8_8187/3899817.html"
                    chapterId = url.split("/")[-1].split(".", 1)[0]
                    chapters.append(
                        {
                            "title": title,
                            "url": url,
                            "chapterId": chapterId,
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
            "extra": {},
        }

    def parse_chapter(
        self,
        html_list: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        """
        Parse a single chapter page and extract clean text or simplified HTML.

        :param html_list: Raw HTML of the chapter page.
        :param chapter_id: Identifier of the chapter being parsed.
        :return: Cleaned chapter content as plain text or minimal HTML.
        """
        if not html_list:
            return None
        tree = html.fromstring(html_list[0], parser=None)

        title_elem = tree.xpath('//div[@class="bookname"]/h1')
        title = "".join(title_elem[0].itertext()).strip() if title_elem else ""
        if not title:
            title = f"第 {chapter_id} 章"

        content_elem = tree.xpath('//div[@id="content"]')
        paragraphs = content_elem[0].xpath(".//p") if content_elem else []
        paragraph_texts = [
            "".join(p.itertext()).strip() for p in paragraphs if p is not None
        ]
        if paragraph_texts and "www.shuhaige.net" in paragraph_texts[-1]:
            paragraph_texts.pop()

        content = "\n".join(paragraph_texts)
        if not content.strip():
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": "shuhaige"},
        }
