#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.dxmwx.parser
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
class DxmwxParser(BaseParser):
    """
    Parser for 大熊猫文学网 book pages.
    """

    site_name: str = "dxmwx"

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
            info_tree.xpath("//span[contains(@style,'font-size: 24px')]/text()")
        )
        author = self._first_str(
            info_tree.xpath(
                "//div[contains(@style,'height: 28px') and contains(., '著')]//a/text()"
            )
        )
        tags = [
            t.strip()
            for t in info_tree.xpath("//span[@class='typebut']//a/text()")
            if t.strip()
        ]
        cover_url = "https://www.dxmwx.org" + self._first_str(
            info_tree.xpath("//img[@class='imgwidth']/@src")
        )

        update_time = self._join_strs(
            info_tree.xpath(
                "//span[starts-with(normalize-space(.), '更新时间：')]/text()"
            ),  # noqa: E501
            replaces=[("更新时间：", "")],
        )
        nodes = info_tree.xpath("(//div[contains(@style,'border-bottom')])[1]/div")
        summary = ""
        if nodes:
            node = nodes[0]
            lines: list[str] = []

            if node.text:
                txt = self._norm_space(node.text)
                if txt:
                    lines.append(txt)

            for child in node.iterchildren():
                if child.tag.lower() == "p" and child.text:
                    txt = self._norm_space(child.text)
                    if txt:
                        lines.append(txt)
                if child.tail:
                    txt = self._norm_space(child.tail)
                    if txt:
                        lines.append(txt)

            summary = "\n".join(lines)

        chapters: list[ChapterInfoDict] = []
        for a in catalog_tree.xpath(
            "//div[contains(@style,'height:40px') and contains(@style,'border-bottom')]//a"  # noqa: E501
        ):
            href = a.get("href") or ""
            title = (a.text_content() or "").strip()
            if not href or not title:
                continue
            # "/read/57215_50197663.html" -> "50197663"
            chap_id = href.split("read/", 1)[-1].split(".html", 1)[0].split("_")[-1]
            chapters.append({"title": title, "url": href, "chapterId": chap_id})
        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
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

        title = self._norm_space(
            self._first_str(tree.xpath("//h1[@id='ChapterTitle']/text()"))
        )
        if not title:
            title = f"第 {chapter_id} 章"

        paragraphs: list[str] = []
        for p in tree.xpath("//div[@id='Lab_Contents']//p"):
            text = (p.text_content() or "").replace("\xa0", " ").replace("\u3000", " ")
            text = text.strip()
            if not text:
                continue
            if "点这里听书" in text or "大熊猫文学" in text:
                continue
            paragraphs.append(text)

        content = "\n".join(paragraphs).strip()
        if not content:
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
