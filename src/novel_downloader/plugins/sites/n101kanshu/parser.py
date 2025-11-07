#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n101kanshu.parser
------------------------------------------------
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
class N101kanshuParser(BaseParser):
    """
    Parser for 101看书 book pages.
    """

    site_name: str = "n101kanshu"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if len(html_list) < 2:
            return None

        info_tree = html.fromstring(html_list[0])
        catalog_tree = html.fromstring(html_list[1])

        def meta(prop: str) -> str:
            return self._first_str(
                info_tree.xpath(f"//meta[@property='{prop}']/@content")
            )

        # --- base info ---
        book_name = meta("og:novel:book_name") or meta("og:title")
        author = meta("og:novel:author")
        cover_url = meta("og:image")
        serial_status = meta("og:novel:status")
        update_time = meta("og:novel:update_time")
        summary = meta("og:description").replace("<br />", "\n")
        tags = [meta("og:novel:category")] if meta("og:novel:category") else []

        wc_nodes = info_tree.xpath("//p[contains(., '字')]/text()")
        word_count = wc_nodes[0].split("|", 1)[0].strip() if wc_nodes else ""

        # --- Chapter volumes & listings ---
        chapters: list[ChapterInfoDict] = []
        for a in catalog_tree.xpath("//ul//a"):
            url = a.get("href", "").strip()
            title = self._first_str(a.xpath(".//text()"))
            if not url:
                continue
            chap_id = url.rsplit("/", 1)[-1].split(".", 1)[0]
            chapters.append(
                {
                    "title": title,
                    "url": url,
                    "chapterId": chap_id,
                }
            )

        if not chapters:
            return None

        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "serial_status": serial_status,
            "word_count": word_count,
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
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        title = self._first_str(tree.xpath("//div[@class='txtnav']//h1/text()"))

        content_nodes = tree.xpath("//div[@id='txtcontent']")
        if not content_nodes:
            return None

        content_div = content_nodes[0]

        def iter_text(node: html.HtmlElement) -> list[str]:
            parts: list[str] = []
            if node.tag in ("script", "style"):
                return parts
            if node.tag == "div" and "txtad" in (node.get("class") or ""):
                return parts

            if node.text and (txt := node.text.strip()):
                parts.append(txt)

            for child in node:
                parts.extend(iter_text(child))
                if child.tail and (tail := child.tail.strip()):
                    parts.append(tail)

            return parts

        paragraphs = iter_text(content_div)

        if not paragraphs:
            return None

        content = "\n".join(paragraphs)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
