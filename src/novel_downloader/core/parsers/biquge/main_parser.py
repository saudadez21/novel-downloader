#!/usr/bin/env python3
"""
novel_downloader.core.parsers.biquge.main_parser
------------------------------------------------

"""

import re
from typing import Any

from lxml import html

from novel_downloader.core.parsers.base import BaseParser
from novel_downloader.models import ChapterDict


class BiqugeParser(BaseParser):
    """ """

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Parse a book info page and extract metadata and chapter structure.

        :param html_list: Raw HTML of the book info page.
        :return: Parsed metadata and chapter structure as a dictionary.
        """
        if not html_list:
            return {}
        tree = html.fromstring(html_list[0])
        result: dict[str, Any] = {}

        def extract_text(elem: html.HtmlElement | None) -> str:
            if elem is None:
                return ""
            return "".join(elem.itertext(tag=None)).strip()

        # 书名
        book_name_elem = tree.xpath('//div[@id="info"]/h1')
        result["book_name"] = extract_text(book_name_elem[0]) if book_name_elem else ""

        # 作者
        author_elem = tree.xpath('//div[@id="info"]/p[1]')
        if author_elem:
            author_text = extract_text(author_elem[0]).replace("\u00a0", "")
            match = re.search(r"作\s*者[:：]?\s*(\S+)", author_text)
            result["author"] = match.group(1).strip() if match else ""
        else:
            result["author"] = ""

        # 封面
        cover_elem = tree.xpath('//div[@id="fmimg"]/img/@src')
        result["cover_url"] = cover_elem[0].strip() if cover_elem else ""

        # 最后更新时间
        update_elem = tree.xpath('//div[@id="info"]/p[3]')
        if update_elem:
            update_text = extract_text(update_elem[0])
            match = re.search(r"最后更新[:：]\s*(\S+)", update_text)
            result["update_time"] = match.group(1).strip() if match else ""
        else:
            result["update_time"] = ""

        # 简介
        intro_elem = tree.xpath('//div[@id="intro"]')
        result["summary"] = extract_text(intro_elem[0]) if intro_elem else ""

        # 卷和章节
        chapters = []
        in_main_volume = False

        list_dl = tree.xpath('//div[@id="list"]/dl')[0]
        for elem in list_dl:
            if elem.tag == "dt":
                text = "".join(elem.itertext()).strip()
                in_main_volume = "正文" in text
            elif in_main_volume and elem.tag == "dd":
                a: list[html.HtmlElement] = elem.xpath("./a")
                if a:
                    title = "".join(a[0].itertext(tag=None)).strip()
                    url = a[0].get("href", "").strip()
                    href_cleaned = url.replace(".html", "")
                    chapter_id_match = re.search(r"/(\d+)$", href_cleaned)
                    chapter_id = chapter_id_match.group(1) if chapter_id_match else ""
                    chapters.append(
                        {"title": title, "url": url, "chapterId": chapter_id}
                    )

        result["volumes"] = [{"volume_name": "正文", "chapters": chapters}]

        return result

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

        # 提取标题
        title_elem = tree.xpath('//div[@class="bookname"]/h1')
        title = "".join(title_elem[0].itertext()).strip() if title_elem else ""
        if not title:
            title = f"第 {chapter_id} 章"

        # 提取内容
        content_elem = tree.xpath('//div[@id="content"]')
        paragraphs = content_elem[0].xpath(".//p") if content_elem else []
        paragraph_texts = [
            "".join(p.itertext()).strip() for p in paragraphs if p is not None
        ]
        content = "\n\n".join([p for p in paragraph_texts if p])
        if not content.strip():
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": "biquge"},
        }
