#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.piaotia.parser
---------------------------------------------

"""

import re
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
class PiaotiaParser(BaseParser):
    """
    Parser for 飘天文学网 book pages.
    """

    site_name: str = "piaotia"

    _RE_DEVICE_DIV = re.compile(
        r'<div\s+id=[\'"“”]?device[\'"“”]?[^>]*>',
        flags=re.IGNORECASE,
    )

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

        book_name = self._first_str(info_tree.xpath("//span[@style]//h1/text()"))
        author = self._first_str(
            info_tree.xpath(
                '//td[contains(text(),"作") and contains(text(),"者")]/text()'
            ),
            replaces=[(chr(0xA0), ""), (" ", ""), ("作者：", "")],
        )

        # Category as tag
        category = self._first_str(
            info_tree.xpath(
                '//td[contains(text(),"类") and contains(text(),"别")]/text()'
            ),
            replaces=[(chr(0xA0), ""), (" ", ""), ("类别：", "")],
        )
        tags = [category] if category else []

        word_count = self._first_str(
            info_tree.xpath('//td[contains(text(),"全文长度")]/text()'),
            replaces=[(chr(0xA0), ""), (" ", ""), ("全文长度：", "")],
        )

        update_time = self._first_str(
            info_tree.xpath('//td[contains(text(),"最后更新")]/text()'),
            replaces=[(chr(0xA0), ""), (" ", ""), ("最后更新：", "")],
        )

        serial_status = self._first_str(
            info_tree.xpath('//td[contains(text(),"文章状态")]/text()'),
            replaces=[(chr(0xA0), ""), (" ", ""), ("文章状态：", "")],
        )

        cover_url = self._first_str(info_tree.xpath('//td[@width="80%"]//img/@src'))

        # Summary
        summary_divs = info_tree.xpath('//td[@width="80%"]/div')
        if summary_divs:
            raw = str(summary_divs[0].text_content())
            summary = raw.split("内容简介：")[-1].strip()
        else:
            summary = ""

        # Chapters (single volume)
        chapters: list[ChapterInfoDict] = []
        for a in catalog_tree.xpath('//div[@class="centent"]//ul/li/a'):
            title = (a.text or "").strip()
            url = a.get("href", "").strip()
            chapter_id = url.split(".")[0]
            chapters.append({"title": title, "url": url, "chapterId": chapter_id})

        # Single volume
        volumes: list[VolumeInfoDict] = [{"volume_name": "正文", "chapters": chapters}]

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "summary": summary,
            "volumes": volumes,
            "tags": tags,
            "word_count": word_count,
            "serial_status": serial_status,
            "extra": {},
        }

    def parse_chapter(
        self,
        html_list: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        """
        Parse chapter page and extract the content of one chapter.

        p.s. 结构好混乱:
        1. `<head>` 没有对应的 `</head>`, 同理 `</body>` 没有对应的 `<body>`
        2. 部分 html 通过 js 直接写入, 例如:
            `document.write("<div id=\"main\" class=\"colors1 sidebar\">");`
        3. 部分 div 的 id 或 style 属性周围的引号是非标准的波浪引号, 例如:
            `<div id=”device” style=”background-color...”>`,
            并也没有对应的 `</div>`

        :param html_list: The HTML list of the chapter pages.
        :param chapter_id: Identifier of the chapter being parsed.
        :return: The chapter's data.
        """
        if not html_list:
            return None

        raw = self._RE_DEVICE_DIV.sub("", html_list[0])
        raw = raw.replace(
            '<script language="javascript">GetMode();</script>',
            '<div id="main" class="colors1 sidebar">',
        ).replace(
            '<script language="javascript">GetFont();</script>',
            '<div id="content">',
        )

        doc = html.fromstring(raw)
        container = doc.xpath('//div[@id="content"]')
        root = container[0] if container else doc

        # Title comes straight from the <h1>
        title = ""
        h1 = root.find(".//h1")
        if h1 is not None:
            full = h1.text_content().strip()
            a_txt = h1.xpath("./a/text()")
            title = full.replace(a_txt[0].strip(), "").strip() if a_txt else full

        # Walk the “script‑tables” -> <br> siblings for the body
        table = root.xpath('.//table[@align="center" and @border]')
        if not table:
            return None
        node = table[0].getnext()

        lines: list[str] = []
        while node is not None:
            # stop at the next table or any bottom‑link nav div
            if (node.tag == "table" and node.get("border")) or (
                node.tag == "div" and node.get("class", "").endswith("link")
            ):
                break

            if node.tag == "br":
                txt = (node.tail or "").replace("\xa0", " ").strip()
                if txt:
                    lines.append(txt)

            node = node.getnext()

        content = "\n".join(lines).strip()
        if not content:
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": self.site_name},
        }
