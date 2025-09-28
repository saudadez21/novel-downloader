#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n37yq.parser
-------------------------------------------

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
class N37yqParser(BaseParser):
    """
    Parser for 哔哩轻小说 book pages.
    """

    site_name: str = "n37yq"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if len(html_list) < 2:
            return None

        info_tree = html.fromstring(html_list[0])
        catalog_tree = html.fromstring(html_list[1])

        book_name = self._first_str(
            info_tree.xpath("//meta[@property='og:novel:book_name']/@content")
            or info_tree.xpath("//h1[contains(@class,'book-name')]/text()")
        )
        author = self._first_str(
            info_tree.xpath("//meta[@property='og:novel:author']/@content")
        )
        cover_url = self._first_str(
            info_tree.xpath("//meta[@property='og:image']/@content")
            or info_tree.xpath("//div[contains(@class,'book-cover')]//img/@src")
        )
        serial_status = self._first_str(
            info_tree.xpath("//meta[@property='og:novel:status']/@content")
            or info_tree.xpath(
                "//div[contains(@class,'book-label')]//a[contains(@class,'state')]/text()"
            )
        )
        word_count = self._first_str(
            info_tree.xpath(
                "//div[contains(@class,'nums')]//span[contains(normalize-space(.),'字数')]//i/text()"
            )
        )
        update_time = self._first_str(
            info_tree.xpath("//meta[@property='og:novel:update_time']/@content")
            or info_tree.xpath(
                "//div[contains(@class,'nums')]//span[contains(normalize-space(.),'更新时间')]//i/text()"
            )
        )

        summary = self._first_str(
            info_tree.xpath("//meta[@property='og:description']/@content"),
            replaces=[("\u3000", " "), ("\xa0", " ")],
        )
        if not summary:
            summary = self._join_strs(
                info_tree.xpath("//div[contains(@class,'book-dec')]//p//text()"),
                replaces=[("<br>", "\n"), ("\u3000", " "), ("\xa0", " ")],
            )

        tags = self._first_str(
            info_tree.xpath("//meta[@property='og:novel:tags']/@content")
        ).split()

        # --- Chapter volumes & listings ---
        volumes: list[VolumeInfoDict] = []
        current_volume_name: str | None = None
        current_chapters: list[ChapterInfoDict] = []

        # Try to iterate each chapter-list <ul> in order
        uls = catalog_tree.xpath("//ul[contains(@class,'chapter-list')]")
        if not uls:
            uls = [catalog_tree]

        def flush_volume() -> None:
            nonlocal current_volume_name, current_chapters
            if current_volume_name is None and current_chapters:
                # If chapters appear before any explicit volume, group them as default
                volumes.append({"volume_name": "正文", "chapters": current_chapters})
            elif current_volume_name is not None:
                volumes.append(
                    {"volume_name": current_volume_name, "chapters": current_chapters}
                )
            current_volume_name = None
            current_chapters = []

        for ul in uls:
            # Iterate direct children in document order: <div class="volume"> and <li>
            for node in ul.iterchildren():
                if not isinstance(node.tag, str):
                    continue
                cls = (node.get("class") or "").strip()
                if node.tag == "div" and "volume" in cls:
                    # Start a new volume; flush the previous one
                    flush_volume()
                    current_volume_name = (node.text_content() or "").strip()
                elif node.tag == "li":
                    a = node.xpath(".//a")
                    if not a:
                        continue
                    a = a[0]
                    title = (a.text or "").strip()
                    url = (a.get("href") or "").strip()
                    if not url:
                        continue
                    chapter_id = url.rsplit("/", 1)[-1].split(".", 1)[0]
                    current_chapters.append(
                        {"title": title, "url": url, "chapterId": chapter_id}
                    )

        # Flush the last collected volume
        flush_volume()

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "serial_status": serial_status,
            "word_count": word_count,
            "summary": summary,
            "update_time": update_time,
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

        title = self._first_str(
            tree.xpath("//div[@id='mlfy_main_text']//h1/text()")
            or tree.xpath("//h1/text()")
        )

        paragraphs: list[str] = []
        content_nodes = tree.xpath("//div[@id='TextContent']/*")
        for node in content_nodes:
            if node.tag == "p":
                txt = (node.text_content() or "").strip()
                if txt:
                    paragraphs.append(txt)
            elif node.tag == "div" and "divimage" in (node.get("class") or ""):
                img = node.xpath(".//img/@src")
                if img:
                    src = img[0].strip()
                    if src:
                        paragraphs.append(f'<img src="{src}" />')

        content = "\n".join(paragraphs)
        if not content:
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
