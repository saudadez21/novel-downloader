#!/usr/bin/env python3
"""
novel_downloader.core.parsers.qianbi.main_parser
------------------------------------------------

"""

from datetime import datetime
from typing import Any

from lxml import html

from novel_downloader.core.parsers.base import BaseParser
from novel_downloader.models import ChapterDict


class QianbiParser(BaseParser):
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

        info_tree = html.fromstring(html_list[0])
        catalog_tree = html.fromstring(html_list[1])
        result: dict[str, Any] = {}

        title = info_tree.xpath('//h1[@class="page-title"]/text()')
        result["book_name"] = title[0].strip() if title else ""

        author = info_tree.xpath('//a[contains(@href,"/author/")]/@title')
        result["author"] = author[0].strip() if author else ""

        cover = info_tree.xpath('//div[@class="novel-cover"]//img/@data-src')
        result["cover_url"] = cover[0].strip() if cover else ""

        status = info_tree.xpath(
            '//a[@class="tag-link" and (text()="完结" or text()="连载")]/text()'
        )
        result["serial_status"] = status[0] if status else ""

        word_count_raw = info_tree.xpath('//span[contains(text(), "万字")]/text()')
        result["word_count"] = word_count_raw[0].strip() if word_count_raw else ""

        summary_node = info_tree.xpath(
            '//div[@class="novel-info-item novel-info-content"]/span'
        )
        if summary_node and summary_node[0] is not None:
            result["summary"] = summary_node[0].text_content().strip()
        else:
            result["summary"] = ""

        result["update_time"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        volumes: list[dict[str, Any]] = []
        current_volume = None

        for elem in catalog_tree.xpath('//div[@class="box"]/*'):
            class_attr = elem.get("class", "")
            class_list = class_attr.split()

            if elem.tag == "h2" and "module-title" in class_list:
                if current_volume:
                    volumes.append(current_volume)
                current_volume = {
                    "volume_name": elem.text.strip() if elem.text else "",
                    "chapters": [],
                }
            elif (
                elem.tag == "div" and "module-row-info" in class_list and current_volume
            ):
                a_tag = elem.xpath('.//a[@class="module-row-text"]')
                if a_tag:
                    title = a_tag[0].xpath(".//span/text()")
                    href = a_tag[0].attrib.get("href", "")
                    if href == "javascript:cid(0)":
                        href = ""
                    chapter_id = (
                        href.split("/")[-1].replace(".html", "") if href else ""
                    )
                    current_volume["chapters"].append(
                        {
                            "title": title[0].strip() if title else "",
                            "url": href,
                            "chapterId": chapter_id,
                        }
                    )

        if current_volume:
            volumes.append(current_volume)

        result["volumes"] = volumes

        return result

    def parse_chapter(
        self,
        html_list: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        """
        Parse a single chapter page and extract clean text or simplified HTML.

        :param html_list: Raw HTML of the chapter page.
        :param chapter_id: Identifier of the chapter being parsed.
        :return: Cleaned chapter content as plain text or minimal HTML.
        """
        if not html_list:
            return None
        tree = html.fromstring(html_list[0])

        paras = tree.xpath('//div[@class="article-content"]/p/text()')
        content_text = "\n\n".join(p.strip() for p in paras if p.strip())
        if not content_text:
            return None

        title = tree.xpath('//h1[@class="article-title"]/text()')
        title_text = title[0].strip() if title else ""

        volume = tree.xpath('//h3[@class="text-muted"]/text()')
        volume_text = volume[0].strip() if volume else ""

        next_href = tree.xpath('//div[@class="footer"]/a[@class="f-right"]/@href')
        next_chapter_id = (
            next_href[0].split("/")[-1].replace(".html", "") if next_href else ""
        )

        return {
            "id": chapter_id,
            "title": title_text,
            "content": content_text,
            "extra": {
                "site": "qianbi",
                "volume": volume_text,
                "next_chapter_id": next_chapter_id,
            },
        }
