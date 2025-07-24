#!/usr/bin/env python3
"""
novel_downloader.core.parsers.piaotia
-------------------------------------

"""

import re
from typing import Any

from lxml import html

from novel_downloader.core.parsers.base import BaseParser
from novel_downloader.core.parsers.registry import register_parser
from novel_downloader.models import ChapterDict


@register_parser(
    site_keys=["piaotia"],
)
class PiaotiaParser(BaseParser):
    """ """

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> dict[str, Any]:
        """
        Parse a book info page and extract metadata and chapter structure.

        :param html_list: Raw HTML of the book info pages.
        :return: Parsed metadata and chapter structure as a dictionary.
        """
        if len(html_list) < 2:
            return {}

        # Parse trees
        info_tree = html.fromstring(html_list[0])
        catalog_tree = html.fromstring(html_list[1])
        result: dict[str, Any] = {}

        # Book name
        book_name = info_tree.xpath("//span[@style]//h1/text()")
        result["book_name"] = book_name[0].strip() if book_name else ""

        # Author
        author_text = info_tree.xpath(
            '//td[contains(text(),"作") and contains(text(),"者")]/text()'
        )
        result["author"] = author_text[0].split("：")[-1].strip() if author_text else ""

        # Category as tag
        category_text = info_tree.xpath(
            '//td[contains(text(),"类") and contains(text(),"别")]/text()'
        )
        category = category_text[0].split("：")[-1].strip() if category_text else ""
        result["tags"] = [category] if category else []

        # Word count
        word_count_text = info_tree.xpath('//td[contains(text(),"全文长度")]/text()')
        result["word_count"] = (
            word_count_text[0].split("：")[-1].strip() if word_count_text else ""
        )

        # Update time
        update_text = info_tree.xpath('//td[contains(text(),"最后更新")]/text()')
        result["update_time"] = (
            update_text[0].split("：")[-1].strip() if update_text else ""
        )

        # Serial status
        status_text = info_tree.xpath('//td[contains(text(),"文章状态")]/text()')
        result["serial_status"] = (
            status_text[0].split("：")[-1].strip() if status_text else ""
        )

        # Cover URL
        cover = info_tree.xpath('//td[@width="80%"]//img/@src')
        result["cover_url"] = cover[0].strip() if cover else ""

        # Summary
        summary_div = info_tree.xpath('//td[@width="80%"]/div')
        if summary_div:
            summary = summary_div[0].xpath("string(.)").split("内容简介：")[-1].strip()
            result["summary"] = summary
        else:
            result["summary"] = ""

        # Chapters (single volume)
        chapters = []
        for a in catalog_tree.xpath('//div[@class="centent"]//ul/li/a'):
            title = a.text.strip()
            url = a.get("href", "")
            chapter_id = url.split(".")[0]
            chapters.append({"title": title, "url": url, "chapterId": chapter_id})

        # Single volume
        result["volumes"] = [{"volume_name": "正文", "chapters": chapters}]

        return result

    def parse_chapter(
        self,
        html_list: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        """
        Parse a single chapter page and extract clean text or simplified HTML.

        p.s. 结构好混乱:
        1. `<head>` 没有对应的 `</head>`, 同理 `</body>` 没有对应的 `<body>`
        2. 部分 html 通过 js 直接写入, 例如:
            `document.write("<div id=\"main\" class=\"colors1 sidebar\">");`
        3. 部分 div 的 id 或 style 属性周围的引号是非标准的波浪引号, 例如:
            `<div id=”device” style=”background-color...”>`,
            并也没有对应的 `</div>`

        :param html_list: Raw HTML of the chapter page.
        :param chapter_id: Identifier of the chapter being parsed.
        :return: Cleaned chapter content as plain text or minimal HTML.
        """
        if not html_list:
            return None

        raw = re.sub(
            r'<div\s+id=[\'"“”]?device[\'"“”]?[^>]*>',
            "",
            html_list[0],
            flags=re.IGNORECASE,
        )
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

        content = "\n\n".join(lines).strip()
        if not content:
            return None

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {"site": "piaotia"},
        }
