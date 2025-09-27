#!/usr/bin/env python3
"""
novel_downloader.plugins.archived.xs63b.parser
----------------------------------------------

"""

import re
from typing import Any

from lxml import html
from novel_downloader.plugins.base.parser import BaseParser
from novel_downloader.schemas import (
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    VolumeInfoDict,
)


class Xs63bParser(BaseParser):
    """
    Parser for 小说路上 book pages.
    """

    site_name: str = "xs63b"

    TITLE_SELECTOR = "//div[@class='block_txt2']//h2/text()"
    AUTHOR_SELECTOR = "//p[contains(., '作者')]/a/text()"
    TYPE_SELECTOR = "//p[contains(., '分类')]/a/text()"
    STATUS_SELECTOR = "//p[contains(., '状态')]/text()"
    UPDATE_SELECTOR = "//p[contains(., '更新')]/text()"
    COVER_SELECTOR = "//div[@class='block_img2']//img/@src"
    SUMMARY_SELECTOR = (
        "//div[@class='intro' and contains(., '小说简介')]"
        "/following-sibling::div[@class='intro_info'][1]"
    )
    CATALOG_ANCHORS = (
        "//h2[contains(., '正文')]/following-sibling::div[@class='book_list'][1]//a"
    )

    CHAPTER_TITLE_SELECTOR = "//h1[@id='_52mb_h1']/text()"
    CHAPTER_PARAGRAPHS = "//div[@id='nr1']//p"

    _RE_STRIP_DIV = re.compile(r"^<div[^>]*>|</div>$", re.I)
    _RE_STRIP_JIANJIE = re.compile(r"^\s*简介\s*[:：]\s*", re.I)

    ADS = {"如章节缺失", "本章未完", "下一页继续阅读", "xs63b.com"}

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if len(html_list) < 2:
            return None

        info_tree = html.fromstring(html_list[0])
        catalog_tree = html.fromstring(html_list[1])

        book_name = self._first_str(info_tree.xpath(self.TITLE_SELECTOR))
        author = self._first_str(info_tree.xpath(self.AUTHOR_SELECTOR))
        book_type = self._first_str(info_tree.xpath(self.TYPE_SELECTOR))

        serial_status = self._first_str(
            info_tree.xpath(self.STATUS_SELECTOR),
            replaces=[("状态：", "")],
        )
        serial_status = self._norm_space(serial_status)

        update_time = self._first_str(
            info_tree.xpath(self.UPDATE_SELECTOR),
            replaces=[("更新：", "")],
        )
        cover_url = self._first_str(info_tree.xpath(self.COVER_SELECTOR))

        # Summary: keep first <br> segment, then cut at "{author}的作品集"
        summary = ""
        nodes = info_tree.xpath(self.SUMMARY_SELECTOR)
        if nodes:
            node_html = html.tostring(nodes[0], method="html", encoding="unicode")
            node_html = self._RE_STRIP_DIV.sub("", node_html).strip()
            first_seg = node_html.split("<br", 1)[0]
            text = html.fromstring(f"<div>{first_seg}</div>").text_content()
            text = self._RE_STRIP_JIANJIE.sub("", text).strip()
            if author:
                text = text.split(f"{author}的作品集")[0].strip()
            summary = text

        tags = [book_type] if book_type else []

        chapters: list[ChapterInfoDict] = []
        for a in catalog_tree.xpath(self.CATALOG_ANCHORS):
            href = a.get("href") or ""
            title = (a.text_content() or "").strip()
            if not href or not title:
                continue
            # 'https://www.xs63b.com/xuanhuan/wanyuzhiwang/29546477.html' -> '29546477'
            chap_id = href.rsplit("/", 1)[-1].split(".")[0]
            chapters.append({"title": title, "url": href, "chapterId": chap_id})

        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "serial_status": serial_status,
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

        title = ""
        paragraphs: list[str] = []

        for html_str in html_list:
            tree = html.fromstring(html_str)

            if not title:
                h1 = self._first_str(tree.xpath(self.CHAPTER_TITLE_SELECTOR))
                title = h1.rsplit(" ", 1)[0].strip() if (" " in h1) else h1

            for p in tree.xpath(self.CHAPTER_PARAGRAPHS):
                cls = p.get("class") or ""
                pid = p.get("id") or ""
                if "hid-pages" in cls or "pages" in cls or "contentTip" in pid:
                    continue

                txt = self._norm_space(p.text_content() or "")
                if not txt or self._is_ad_line(txt):
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
