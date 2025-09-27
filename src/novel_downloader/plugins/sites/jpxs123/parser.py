#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.jpxs123.parser
---------------------------------------------

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
class Jpxs123Parser(BaseParser):
    """
    Parser for 精品小说网 book pages.
    """

    site_name: str = "jpxs123"
    BASE_URL = "https://www.jpxs123.com"

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

        author = self._first_str(tree.xpath('//div[@class="date"]/span[1]//a/text()'))
        update_time = self._first_str(
            tree.xpath('//div[@class="date"]/span[2]/text()'), replaces=[("时间：", "")]
        )
        cover_rel = self._first_str(tree.xpath('//div[@class="pic"]/img/@src'))
        cover_url = (
            f"{self.BASE_URL}{cover_rel}"
            if cover_rel and not cover_rel.startswith("http")
            else cover_rel
        )

        # Summary from the <p> inside infos
        summary = self._join_strs(tree.xpath('//div[@class="infos"]/p//text()'))

        # Chapters from the book_list
        chapters: list[ChapterInfoDict] = []
        for a in tree.xpath('//div[contains(@class,"book_list")]//li/a'):
            url = a.get("href", "").strip()
            title = a.text_content().strip()
            # General regex: /{category}/{bookId}/{chapterId}.html
            cid = url.split("/")[-1].split(".")[0]
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
            "cover_url": cover_url,
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
        true_link = link.replace("xs../", "/e/DownSys/")
        return f"{cls.BASE_URL}{true_link}"
