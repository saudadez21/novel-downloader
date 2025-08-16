#!/usr/bin/env python3
"""
novel_downloader.core.parsers.xshbook
-------------------------------------

"""

import re
from datetime import datetime
from typing import Any
from urllib.parse import urljoin

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
    site_keys=["xshbook"],
)
class XshbookParser(BaseParser):
    """Parser for 小说虎 book pages."""

    BASE = "http://www.xshbook.com"

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

        book_name = self._first_str(tree.xpath("//div[@id='info']/h1/text()"))

        author_raw = self._first_str(
            [
                html.tostring(node, method="text", encoding="unicode")
                for node in tree.xpath(
                    "//div[@id='info']/p[1] | //div[@id='info']/p[contains(., '作')]"
                )
            ]
        )
        author = re.sub(r"^作\s*[\u00A0\s]*者[:：]\s*", "", author_raw).strip()

        update_time = self._first_str(
            tree.xpath("//meta[@property='og:novel:update_time']/@content")
        )
        if not update_time:
            update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        intro_ps = tree.xpath("//div[@id='intro']//p")
        summary = "\n".join(
            self._clean_text(html.tostring(p, method="text", encoding="unicode"))
            for p in intro_ps
        ).strip()
        summary = summary.split("本站提示", 1)[0].strip()

        cover_url = self._first_str(tree.xpath("//div[@id='fmimg']//img/@src"))
        if cover_url:
            cover_url = urljoin(self.BASE, cover_url)

        book_type = self._first_str(tree.xpath("//div[@class='con_top']/a[2]/text()"))
        tags: list[str] = [book_type] if book_type else []

        chapters: list[ChapterInfoDict] = []
        for a in tree.xpath("//div[@id='list']//dd/a"):
            href = a.get("href", "")
            title = self._clean_text(a.text_content())
            url = urljoin(self.BASE, href) if href else ""
            chapter_id = self._chapter_id_from_href(href) if href else ""
            if title and url and chapter_id:
                chapters.append({"title": title, "url": url, "chapterId": chapter_id})

        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
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
        """
        Parse a single chapter page and extract clean text or simplified HTML.

        :param html_list: Raw HTML of the chapter page.
        :param chapter_id: Identifier of the chapter being parsed.
        :return: Cleaned chapter content as plain text or minimal HTML.
        """
        if not html_list:
            return None
        tree = html.fromstring(html_list[0], parser=None)

        title = self._first_str(tree.xpath("//div[@class='bookname']/h1/text()"))
        if not title:
            title = self._first_str(
                tree.xpath("//div[@class='con_top']/text()[last()]")
            )

        cont_nodes = tree.xpath("//div[@id='content']")
        if not cont_nodes:
            return None
        cont = cont_nodes[0]

        # remove scripts under content
        for s in cont.xpath(".//script"):
            s.getparent().remove(s)

        paragraphs: list[str] = []
        for p in cont.xpath(".//p"):
            text = html.tostring(p, method="text", encoding="unicode")
            text = text.replace("\xa0", " ")
            # remove trailing inline numeric artifacts like <span>1</span>
            text = re.sub(r"(?:\s*\d+\s*)+$", "", text).strip()
            # filter boilerplate lines
            bad = (
                "谨记我们的网址" in text
                or "温馨提示" in text
                or "提示" in text
                and "本文" not in text
                and len(text) < 60
                or "分享" in text
                and len(text) < 40
            )
            if not bad:
                paragraphs.append(text)

        content = "\n".join(self._clean_text(p) for p in paragraphs if p.strip())
        if not content.strip():
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": "xshbook"},
        }

    @staticmethod
    def _clean_text(s: str) -> str:
        """
        Normalize whitespace and remove common boilerplate artifacts.
        """
        s = s.replace("\xa0", " ")  # nbsp to space
        s = re.sub(r"[ \t]+", " ", s)  # collapse spaces
        s = re.sub(r" *\n *(?=\n)", "\n", s)  # trim spaces around blank lines
        return s.strip()

    @staticmethod
    def _chapter_id_from_href(href: str) -> str:
        """
        Extract a stable chapter id from a chapter href.

        Examples:
            /95071/95071941/389027455.html -> "389027455"
            /93975/93975003/19095313.html  -> "19095313"
        """
        path = href.split("?", 1)[0].rstrip("/")
        filename = path.rsplit("/", 1)[-1]
        if filename.endswith(".html"):
            filename = filename[:-5]
        return filename or path.strip("/").split("/")[-1]
