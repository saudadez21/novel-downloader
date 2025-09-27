#!/usr/bin/env python3
"""
novel_downloader.plugins.archived.deqixs.parser
-----------------------------------------------

"""

from typing import Any

from lxml import html
from novel_downloader.plugins.base.parser import BaseParser
from novel_downloader.schemas import (
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    VolumeInfoDict,
)


class DeqixsParser(BaseParser):
    """
    Parser for 得奇小说网 book pages.
    """

    ADS: set[str] = {
        "更新不易",
        "记得分享",
        "(本章完)",
    }

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        # Extract book title and word count
        book_name = tree.xpath("//div[@class='itemtxt']/h1/a/text()")[0].strip()
        word_count = tree.xpath("//div[@class='itemtxt']/h1/i/text()")[0].strip()

        # Extract serialization status and genre tags
        spans = tree.xpath("//div[@class='itemtxt']/p[1]/span/text()")
        serial_status = spans[0].strip() if spans else ""
        tags = [s.strip() for s in spans[1:-1]] if len(spans) > 2 else []

        # Extract author
        author_text = tree.xpath("//div[@class='itemtxt']/p[2]/a/text()")[0]
        author = author_text.replace("作者：", "").strip()

        # Extract cover URL
        cover_src = tree.xpath("//div[@class='item']//a/img/@src")[0]
        cover_url = "https:" + cover_src if cover_src.startswith("//") else cover_src

        # Extract last update time
        update_raw = tree.xpath("//h2[@id='dir']/span/text()")[0].strip()
        update_time = update_raw.replace("更新时间：", "").strip()

        # Extract summary paragraphs (first description block)
        paras = tree.xpath("(//div[@class='des bb'])[1]/p/text()")
        summary = "\n".join(p.strip() for p in paras if p.strip())

        # Extract chapters list
        chapter_nodes = tree.xpath("//div[@id='list']//ul/li/a")
        chapters: list[ChapterInfoDict] = []
        for a in chapter_nodes:
            href = a.get("href")
            chapter_id = href.split("/")[-1].replace(".html", "")
            title = a.text_content().strip()
            chapters.append({"title": title, "url": href, "chapterId": chapter_id})

        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "serial_status": serial_status,
            "word_count": word_count,
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

        title_text = ""
        contents: list[str] = []
        for curr_html in html_list:
            tree = html.fromstring(curr_html)
            # Extract title once
            if not title_text:
                full_title = tree.xpath("string(//div[@class='submenu']/h1)")
                if ">" in full_title:
                    title_text = full_title.split(">", 1)[1].strip()
                else:
                    title_text = full_title.strip()
            # Extract paragraphs
            for p in tree.xpath("//div[@class='con']/p"):
                text = p.text_content().strip()
                # Filter out ads or empty paragraphs
                if not text or any(ad in text for ad in self.ADS):
                    continue
                contents.append(text)

        content = "\n".join(contents)
        if not content:
            return None

        return {
            "id": chapter_id,
            "title": title_text,
            "content": content,
            "extra": {"site": "deqixs"},
        }
