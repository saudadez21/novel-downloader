#!/usr/bin/env python3
"""
novel_downloader.core.parsers.xshbook
-------------------------------------

"""

from typing import Any

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
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        book_name = self._first_str(tree.xpath("//div[@id='info']/h1/text()"))

        author = self._first_str(
            tree.xpath("//div[@id='info']/p[1]/text()"),
            replaces=[("\xa0", ""), ("作者:", "")],
        )

        update_time = self._first_str(
            tree.xpath("//meta[@property='og:novel:update_time']/@content")
        )

        summary = "\n".join(
            self._first_str(p.xpath("string()").splitlines())
            for p in tree.xpath("//div[@id='intro']//p")
        ).strip()
        summary = summary.split("本站提示", 1)[0].strip()

        cover_url = self._first_str(tree.xpath("//div[@id='fmimg']//img/@src"))

        book_type = self._first_str(tree.xpath("//div[@class='con_top']/a[2]/text()"))
        tags: list[str] = [book_type] if book_type else []

        chapters: list[ChapterInfoDict] = []
        for a in tree.xpath("//div[@id='list']//dd/a"):
            href = a.get("href", "")
            title = self._norm_space(a.text_content())
            # /95071/95071941/389027455.html -> "389027455"
            chapter_id = href.rsplit("/", 1)[-1].split(".", 1)[0]
            chapters.append({"title": title, "url": href, "chapterId": chapter_id})

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
        if not html_list:
            return None
        tree = html.fromstring(html_list[0])

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

        content = "\n".join(self._norm_space(p) for p in paragraphs if p.strip())
        if not content.strip():
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": "xshbook"},
        }
