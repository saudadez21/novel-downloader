#!/usr/bin/env python3
"""
novel_downloader.plugins.common.parser.biquge4
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


class Biquge4Parser(BaseParser):
    """
    Base Parser for biquge-related book pages.
    """

    ADS = {
        "关闭小说畅读模式体验更好",
        "内容未完，下一页继续阅读",
        "本章阅读完毕，更多请搜索",
    }
    BASE_URL: str

    NOVELCONTENT_RE = re.compile(
        r'<div[^>]*id=["\']novelcontent["\'][^>]*>(.*?)</div>',
        re.S | re.I,
    )
    TITLE_RE = re.compile(
        r"<h1[^>]*>(.*?)</h1>",
        re.S | re.I,
    )
    TAG_RE = re.compile(r"<[^>]+>")
    P_BR_RE = re.compile(r"</?p\s*[^>]*>|<br\s*/?>", re.I)

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        # --- Basic meta extraction ---
        book_name = self._first_str(
            tree.xpath('//meta[@property="og:novel:book_name"]/@content')
        )
        if not book_name:
            book_name = self._first_str(
                tree.xpath('//div[contains(@class,"catalog1")]/h1/text()')
            )

        author = self._first_str(
            tree.xpath('//meta[@property="og:novel:author"]/@content')
        )
        if not author:
            author = self._first_str(
                tree.xpath('//p[contains(@class,"p1")]/text()'),
                replaces=[("作者：", "")],
            )

        cover_url = self._first_str(tree.xpath('//meta[@property="og:image"]/@content'))
        if not cover_url:
            cover_url = self._first_str(
                tree.xpath('//div[contains(@class,"tu")]/img/@src')
            )
        if cover_url.startswith("//"):
            cover_url = "https:" + cover_url
        elif cover_url.startswith("/"):
            cover_url = self.BASE_URL + cover_url

        update_time = self._first_str(
            tree.xpath('//meta[@property="og:novel:update_time"]/@content')
        )
        if not update_time:
            update_time = self._first_str(
                tree.xpath(
                    '//p[contains(@class,"p2") and contains(text(),"更新")]/text()'
                ),
                replaces=[("更新：", "")],
            )

        serial_status = self._first_str(
            tree.xpath('//meta[@property="og:novel:status"]/@content')
        )
        category = self._first_str(
            tree.xpath('//meta[@property="og:novel:category"]/@content')
        )
        tags = [category] if category else []

        summary = self._first_str(
            tree.xpath('//meta[@property="og:description"]/@content')
        )
        if not summary:
            summary = self._join_strs(
                tree.xpath('//div[contains(@class,"jj")]//text()')
            )
            summary = summary.split("最后观看小说就不会弹出畅读模式了。", 1)[-1]
            summary = summary.rsplit("最新章节推荐地址", 1)[0].strip()

        # --- Chapter list ---
        chapters: list[ChapterInfoDict] = []
        # Find the section that has “全部章节”
        for elem in tree.xpath('//div[contains(@class,"info_chapters")]/*'):
            tag = (elem.tag or "").lower()
            e_cls = (elem.get("class") or "").lower()
            if tag == "ul" and "p2" in e_cls:
                # After "全部章节" block
                if "全部章节" not in elem.getprevious().text_content():
                    continue
                for a in elem.xpath(".//a"):
                    href = (a.get("href") or "").strip()
                    if not href:
                        continue
                    chap_title = (a.text_content() or "").strip()
                    chap_id = href.rsplit("/", 1)[-1].split(".", 1)[0]
                    chapters.append(
                        {
                            "title": chap_title,
                            "url": href,
                            "chapterId": chap_id,
                        }
                    )

        if not chapters:
            # fallback: take all <a> in info_chapters
            for a in tree.xpath('//div[contains(@class,"info_chapters")]//a'):
                href = (a.get("href") or "").strip()
                if not href:
                    continue
                chap_title = (a.text_content() or "").strip()
                chap_id = href.rsplit("/", 1)[-1].split(".", 1)[0]
                chapters.append(
                    {
                        "title": chap_title,
                        "url": href,
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
        """
        章节正文所在的 `<div id="novelcontent">` 内含有大量未闭合或嵌套错误的标签
        (如 `<tr>`, `<table>`, `<td>` 等)

        导致使用 `lxml` 时结构混乱, 因此这里采用正则表达式来截取该 DIV 内容并手动清理
        """
        if not html_list:
            return None

        title = ""
        paragraphs: list[str] = []

        for curr_html in html_list:
            if not title:
                m_titles = self.TITLE_RE.findall(curr_html)
                if m_titles:
                    title = self.TAG_RE.sub("", m_titles[-1])
                    title = title.rsplit("(", 1)[0].strip()

            m = self.NOVELCONTENT_RE.search(curr_html)
            if not m:
                continue
            raw_html = m.group(1)

            text = raw_html.replace("&nbsp;", " ")
            text = self.P_BR_RE.sub("\n", text)  # p/br -> newline
            text = self.TAG_RE.sub("", text)  # strip other tags

            for line in text.splitlines():
                line = line.strip()
                if not line or self._is_ad_line(line):
                    continue
                paragraphs.append(line)

        if not paragraphs:
            return None

        content = "\n".join(paragraphs)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
