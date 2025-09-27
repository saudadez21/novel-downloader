#!/usr/bin/env python3
"""
novel_downloader.plugins.archived.xiaoshuoge.parser
---------------------------------------------------

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


class XiaoshuogeParser(BaseParser):
    """
    Parser for 小说屋 (xiaoshuoge.info).
    """

    site_name: str = "xiaoshuoge"
    AD_STR: str = "小说屋 www.xiaoshuoge.info"

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

        book_name = self._first_str(
            info_tree.xpath('//meta[@property="og:novel:book_name"]/@content')
        )
        author = self._first_str(
            info_tree.xpath('//meta[@property="og:novel:author"]/@content')
        )

        # Category -> tags
        cat_val = self._first_str(
            info_tree.xpath('//meta[@property="og:novel:category"]/@content')
        )
        tags = [cat_val] if cat_val else []

        word_count = self._first_str(
            info_tree.xpath(
                '//table[@class="hide"]//td[contains(text(),"全文字数")]/text()'
            ),
            replaces=[("全文字数：", "")],
        )
        update_time = self._first_str(
            info_tree.xpath(
                '//table[@class="hide"]//td[contains(text(),"最后更新")]/text()'
            ),
            replaces=[("最后更新：", "")],
        )
        serial_status = self._first_str(
            info_tree.xpath(
                '//table[@class="hide"]//td[contains(text(),"连载状态")]/text()'
            ),
            replaces=[("连载状态：", "")],
        )

        cover_url = self._first_str(
            info_tree.xpath('//meta[@property="og:image"]/@content')
        )

        # Summary
        summary_div = info_tree.xpath('//div[@class="tabvalue"][1]//div')
        summary: str = summary_div[0].text_content().strip() if summary_div else ""

        # Chapters (single volume)
        chapters: list[ChapterInfoDict] = []
        chapter_links = catalog_tree.xpath(
            '//ul[contains(@class,"chapters")]//li[contains(@class,"chapter")]/a'
        )
        for a in chapter_links:
            url = a.get("href", "").strip()
            title = a.text_content().strip()
            # chapterId is the numeric filename before ".html"
            chapter_id = url.rsplit("/", 1)[-1].split(".")[0]
            chapters.append({"title": title, "url": url, "chapterId": chapter_id})

        # Single volume
        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "word_count": word_count,
            "serial_status": serial_status,
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
        if not html_list:
            return None

        doc = html.fromstring(html_list[0])
        # main container
        content_divs = doc.xpath('//div[@id="acontent"]')
        if not content_divs:
            return None
        container = content_divs[0]

        # Get the <h1> title
        title_elem = container.find("h1")
        title = title_elem.text_content().strip() if title_elem is not None else ""

        paras: list[str] = []
        started = False
        for node in container.xpath("./*"):
            # anchor: first <div id="content_tip">
            if node.tag == "div" and node.get("id") == "content_tip":
                raw = node.tail or ""
                # drop any "(小说屋 ...)" prefix before the real text
                if ")" in raw:
                    raw = raw.split(")", 1)[1]
                first_line = raw.lstrip("\ufeff").strip()
                if first_line:
                    paras.append(first_line)
                started = True
                continue

            if not started:
                continue

            # stop collecting once we hit any div
            cls_name = node.get("class") or ""
            if node.tag == "div" and any(
                k in cls_name for k in ("tishi", "footlink", "fullbar")
            ):
                break

            # grab each <br/> tail as a paragraph
            if node.tag == "br":
                line = (node.tail or "").strip()
                if not line or self.AD_STR in line:
                    continue
                paras.append(line)

        if not paras:
            return None
        content = "\n".join(paras)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
