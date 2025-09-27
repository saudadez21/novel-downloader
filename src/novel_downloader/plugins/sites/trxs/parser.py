#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.trxs.parser
------------------------------------------

"""

from typing import Any

from lxml import html

from novel_downloader.plugins.registry import registrar
from novel_downloader.plugins.sites.tongrenquan.parser import TongrenquanParser
from novel_downloader.schemas import (
    BookInfoDict,
    ChapterInfoDict,
    VolumeInfoDict,
)


@registrar.register_parser()
class TrxsParser(TongrenquanParser):
    """
    Parser for 同人小说网 book pages.
    """

    site_name: str = "trxs"
    BASE_URL = "https://www.trxs.cc"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        # Metadata
        book_name = self._first_str(tree.xpath('//div[@class="infos"]/h1/text()'))
        author = self._first_str(tree.xpath('//div[@class="date"]/span/a/text()'))
        cover_url = self.BASE_URL + self._first_str(
            tree.xpath('//div[@class="pic"]//img/@src')
        )
        update_time = self._first_str(
            tree.xpath('//div[@class="date"]/text()[normalize-space()]'),
            replaces=[("日期：", "")],
        )

        # Summary (collapse text within the <p> tag)
        paras = tree.xpath('//div[@class="infos"]/p//text()')
        summary = "\n".join(p.strip() for p in paras if p.strip())

        # Chapters extraction
        chapters: list[ChapterInfoDict] = [
            {
                "title": (a.text or "").strip(),
                "url": (a.get("href") or "").strip(),
                "chapterId": (a.get("href") or "").rsplit("/", 1)[-1].split(".", 1)[0],
            }
            for a in tree.xpath('//div[contains(@class,"book_list")]//ul//li/a')
        ]
        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "tags": ["同人小说"],
            "summary": summary,
            "volumes": volumes,
            "extra": {},
        }
