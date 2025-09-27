#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.yibige.parser
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
class YibigeParser(BaseParser):
    """
    Parser for 一笔阁 book pages.
    """

    site_name: str = "yibige"
    ADS = {
        "首发无广告",
        "请分享",
        "读之阁",
        "小说网",
        "首发地址",
        "手机阅读",
        "一笔阁",
        "site_con_ad",
        "chapter_content",
    }

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if len(html_list) < 2:
            return None

        # Parse trees
        info_tree = html.fromstring(html_list[0])
        catalog_tree = html.fromstring(html_list[1])

        # --- From <meta> data ---
        book_name = self._meta(info_tree, "og:novel:book_name") or self._first_str(
            info_tree.xpath("//div[@id='info']/h1/text()")
        )

        author = self._meta(info_tree, "og:novel:author") or self._first_str(
            info_tree.xpath("//div[@id='info']/p[a]/a/text()")
        )

        cover_url = self._meta(info_tree, "og:image") or self._first_str(
            info_tree.xpath("//div[@id='fmimg']//img/@src")
        )

        update_time = self._meta(info_tree, "og:novel:update_time").replace("T", " ")
        serial_status = self._meta(info_tree, "og:novel:status") or "连载中"

        word_count = self._first_str(
            info_tree.xpath("//div[@id='info']/p[contains(., '字数：')]/text()[1]"),
            replaces=[("字数：", "")],
        )

        # Summary: first paragraph under #intro
        summary = self._first_str(info_tree.xpath("//div[@id='intro']//p[1]/text()"))

        # Category and tags
        book_type = self._meta(info_tree, "og:novel:category")
        tags_set = set(self._meta_all(info_tree, "book:tag"))
        if book_type:
            tags_set.add(book_type)
        tags = list(tags_set)

        # --- Chapters from the catalog page ---
        chapters: list[ChapterInfoDict] = []
        for a in catalog_tree.xpath("//div[@id='list']/dl/dd/a"):
            href = (a.get("href") or "").strip()
            if not href:
                continue
            title = (a.text_content() or "").strip()
            if not title:
                continue
            # /6238/2496.html -> 2496
            chap_id = href.split("/")[-1].split(".")[0]
            chapters.append({"title": title, "url": href, "chapterId": chap_id})

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
        tree = html.fromstring(html_list[0])

        title = self._first_str(tree.xpath("//div[@class='bookname']/h1/text()"))

        paragraphs: list[str] = []
        for p in tree.xpath("//div[@id='content']//p"):
            txt = self._norm_space(p.text_content())
            if not txt or self._is_ad(txt):
                continue
            paragraphs.append(txt)

        content = "\n".join(paragraphs).strip()
        if not content:
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }

    def _is_ad(self, s: str) -> bool:
        """
        Filter for footer junk inside #content.
        """
        if self._is_ad_line(s):
            return True

        ss = s.replace(" ", "")
        # return any(b in s or b in ss for b in self.ADS)
        return self._is_ad_line(ss)

    @classmethod
    def _meta(cls, tree: html.HtmlElement, prop: str) -> str:
        """
        Get a single meta property content
        """
        return cls._first_str(tree.xpath(f"//meta[@property='{prop}']/@content"))

    @staticmethod
    def _meta_all(tree: html.HtmlElement, prop: str) -> list[str]:
        """
        Get all meta property content values
        """
        return tree.xpath(f"//meta[@property='{prop}']/@content") or []
