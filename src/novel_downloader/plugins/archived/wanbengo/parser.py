#!/usr/bin/env python3
"""
novel_downloader.plugins.archived.wanbengo.parser
-------------------------------------------------

"""

import re
from html import unescape
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
class WanbengoParser(BaseParser):
    """
    Parser for 完本神站 book pages.
    """

    site_name: str = "wanbengo"

    # XPaths for the chapter page
    _CHAP_SPLIT_RE = re.compile(r"(?:</p\s*>|<p\b[^>]*>|<br\s*/?>)", re.I)
    _CHAP_READERCON_RE = re.compile(
        r'<div[^>]*class=(?:"[^"]*readerCon[^"]*"|\'[^\']*readerCon[^\']*\')[^>]*>(.*?)</div>',
        re.I | re.S,
    )
    _TAGS_RE = re.compile(r"<[^>]+>")
    _SCRUB_RUNS_RE = re.compile(r"[_?]{2,}")
    _SCRUB_TAIL_RE = re.compile(r"\s*（未完待续.*?$")

    # fmt: off
    ADS = {
        "完本神站", "本站网址", "报错", "键盘", "客户端", "收藏", "书架",
        "猜你喜欢", "上一章", "下一章", "章节目录", "LastRead", "贴吧",
        "倾心打造", "全文无错", "分享本站", "点此章节报错", "温馨提示", "域名",
        r"wanbentxt\.com", r"wanbengo\.com",
    }
    # fmt: on
    _PUNCT_ONLY = re.compile(
        r"^[\s\W_·—\-･。，、；;：:！!？?\(\)（）【】《》“”\"'…·]+$"
    )  # noqa: E501

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        book_name = self._first_str(
            tree.xpath("//div[@class='detailTopMid']//h1/text()")
        )
        author = self._first_str(
            tree.xpath("//div[@class='detailTopMid']//div[@class='writer']//a/text()")
        )
        cover_url = self._first_str(
            tree.xpath("//div[@class='detailTopLeft']//img/@src")
        )
        serial_status = self._first_str(
            tree.xpath(
                "//div[@class='detailTopLeft']//span[contains(@class,'end')]/text()"
            )
        )
        word_count = self._first_str(
            tree.xpath(
                "//div[@class='detailTopMid']//table//tr[td/span[contains(text(),'字数')]]/td[last()]/text()"
            )
        )
        summary = self._first_str(
            tree.xpath(
                "//div[@class='detailTopMid']//table//tr[td/span[contains(text(),'简介')]]/td[last()]//text()"
            )
        )

        book_type = self._first_str(tree.xpath("//div[@class='route']/a[2]//text()"))
        tags = [book_type] if book_type else []

        update_time = (
            m.group(1)
            if (
                m := re.search(
                    r"\b(\d{4}-\d{2}-\d{2})\b",
                    tree.xpath("string(//div[@class='chapterTitle']//span)"),
                )
            )
            else ""
        )

        chapters: list[ChapterInfoDict] = []
        for a in tree.xpath("//div[@class='chapter']//ul//li/a"):
            title = self._first_str(a.xpath(".//text()"))
            href = a.get("href") or ""
            # "/129/103950.html" -> "103950"
            cid = href.rstrip(".html").split("/")[-1]
            chapters.append({"title": title, "url": href, "chapterId": cid})

        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "word_count": word_count,
            "summary": summary,
            "tags": tags,
            "volumes": volumes,
            "serial_status": serial_status,
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

        inner = self._CHAP_READERCON_RE.search(html_list[0])
        if not inner:
            return None

        tree = html.fromstring(html_list[0])
        title = self._first_str(
            tree.xpath("//div[contains(@class,'readerTitle')]//h2/text()")
        )

        parts = self._CHAP_SPLIT_RE.split(inner.group(1))
        paragraphs: list[str] = []
        for part in parts:
            if not part:
                continue
            s = self._TAGS_RE.sub("", part)
            s = unescape(s).replace("\xa0", " ")
            if self._is_noise_line(s):
                continue
            s = self._norm_space(self._scrub_ascii_gibberish(s.strip()))
            if s:
                paragraphs.append(s)

        if not paragraphs:
            return None

        content = "\n".join(paragraphs)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }

    def _is_noise_line(self, s: str) -> bool:
        """Heuristic to drop obvious ad/footer/noise lines."""
        if not s.strip():
            return True
        if self._is_ad_line(s):
            return True
        if self._PUNCT_ONLY.match(s):
            return True
        return False

    @classmethod
    def _scrub_ascii_gibberish(cls, s: str) -> str:
        """
        Remove common injected ASCII junk like long runs of '?' or '_'
        while keeping normal text intact.
        """
        s = s.replace("()?()", "").replace("[(．)]", "")
        s = s.replace("．", ".")
        s = cls._SCRUB_RUNS_RE.sub("", s)  # drop runs like ???? or ____
        s = cls._SCRUB_TAIL_RE.sub("", s)
        return s.strip()
