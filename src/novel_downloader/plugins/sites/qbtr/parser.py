#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.qbtr.parser
------------------------------------------

"""

import re
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
class QbtrParser(BaseParser):
    """
    Parser for 全本同人小说 book pages.
    """

    site_name: str = "qbtr"
    BASE_URL = "https://www.qbtr.cc"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        # Parse the main info page
        tree = html.fromstring(html_list[0])
        # Book name
        book_name = self._first_str(tree.xpath('//div[@class="infos"]/h1/text()'))
        # Tags: the second breadcrumb (e.g., "同人小说")
        tag = self._first_str(
            tree.xpath('//div[contains(@class,"menNav")]/a[2]/text()')
        )
        tags = [tag] if tag else []

        # Author & update_time from the date div
        date_div = tree.xpath('//div[@class="date"]')
        date_text = html.tostring(date_div[0], encoding="unicode", method="text")
        author_match = re.search(r"作者[：:]\s*([^日]+)", date_text)
        author = author_match.group(1).strip() if author_match else ""
        date_match = re.search(r"日期[：:]\s*([\d-]+)", date_text)
        update_time = date_match.group(1) if date_match else ""

        # Summary from the <p> inside infos
        paras = tree.xpath('//div[@class="infos"]/p//text()')
        summary = "\n".join(p.strip() for p in paras if p.strip())

        # Chapters from the book_list
        chapters: list[ChapterInfoDict] = []
        for a in tree.xpath('//div[contains(@class,"book_list")]//li/a'):
            url = a.get("href", "").strip()
            title = a.text_content().strip()
            # General regex: /{category}/{bookId}/{chapterId}.html
            m = re.search(r"^/[^/]+/\d+/(\d+)\.html$", url)
            cid = m.group(1) if m else ""
            chapters.append({"title": title, "url": url, "chapterId": cid})

        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        # Parse the download page (second HTML)
        download_url = ""
        if len(html_list) > 1 and html_list[1]:
            dtree = html.fromstring(html_list[1])
            a = dtree.xpath('//a[@id="dowloadnUrl"]')
            if a:
                link = a[0].get("link") or a[0].get("href") or ""
                download_url = self._fix_download_link(link)

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": "",
            "update_time": update_time,
            "tags": tags,
            "summary": summary,
            "volumes": volumes,
            "extra": {"download_url": download_url},
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

        raw_title = self._first_str(
            tree.xpath('//div[contains(@class,"read_chapterName")]//h1/text()')
        )

        crumbs = tree.xpath('//div[contains(@class,"readTop")]//a/text()')
        book_name = crumbs[-1].strip() if crumbs else ""

        title = raw_title.replace(book_name, "").strip()

        paragraphs = tree.xpath('//div[contains(@class,"read_chapterDetail")]/p')
        texts = []
        for p in paragraphs:
            txt = p.text_content().strip()
            if txt:
                texts.append(txt)

        content = "\n".join(texts)
        if not content:
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }

    @classmethod
    def _fix_download_link(cls, link: str) -> str:
        true_link = link.replace("qb../", "/e/DownSys/")
        return f"{cls.BASE_URL}{true_link}"
