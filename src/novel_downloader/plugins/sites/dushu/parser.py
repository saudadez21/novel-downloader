#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.dushu.parser
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
class DushuParser(BaseParser):
    """
    Parser for 读书 book pages.
    """

    site_name: str = "dushu"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        # --- Basic metadata ---
        book_name = self._first_str(tree.xpath("//div[@class='book-title']/h1/text()"))
        author = self._first_str(
            tree.xpath(
                "//div[@class='book-details']//table//tr[td[contains(., '作')]]/td[2]/text()"  # noqa: E501
            )
        )
        cover_url = self._first_str(tree.xpath("//div[@class='book-pic']//img/@src"))

        summary = self._join_strs(
            tree.xpath("//div[contains(@class,'txtsummary')]//text()"),
            replaces=[("\u3000", ""), ("\xa0", ""), ("　", "")],
        )

        # --- Volumes & chapters ---
        volumes: list[VolumeInfoDict] = []

        volume_nodes = tree.xpath(
            "//div[@class='book-summary']//div[@class='book-chapter']"
        )
        for idx, vol_node in enumerate(volume_nodes, start=1):
            vol_name = (vol_node.text_content() or "").strip() or f"未命名卷 {idx}"

            # Find the following table of chapters
            table = vol_node.xpath("following-sibling::table[1]")
            if not table:
                continue

            vol_chaps: list[ChapterInfoDict] = []
            for a in table[0].xpath(".//a"):
                href = a.get("href") or ""
                if not href:
                    continue
                chap_id = href.rsplit("/", 1)[-1].split(".", 1)[0]
                title = (a.text_content() or "").strip()
                vol_chaps.append(
                    {
                        "title": title,
                        "url": href,
                        "chapterId": chap_id,
                    }
                )

            if vol_chaps:
                volumes.append(
                    {
                        "volume_name": vol_name,
                        "chapters": vol_chaps,
                    }
                )

        if not volumes:
            return None

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": "",
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

        title = self._first_str(
            tree.xpath(
                "//p[contains(@class,'text-center') and contains(@class,'text-large')]/text()"  # noqa: E501
            )
        )

        paragraphs = [
            s
            for p in tree.xpath("//div[@class='content_txt']//text()")
            if (s := p.strip())
        ]

        if not paragraphs:
            return None

        content = "\n".join(paragraphs)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
