#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n23qb.parser
-------------------------------------------

"""

from datetime import datetime
from typing import Any

from lxml import html

from novel_downloader.plugins.base.parser import BaseParser
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import (
    BookInfoDict,
    ChapterDict,
    VolumeInfoDict,
)


@registrar.register_parser()
class N23qbParser(BaseParser):
    """
    Parser for 铅笔小说 book pages.
    """

    site_name: str = "n23qb"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if len(html_list) < 2:
            return None

        info_tree = html.fromstring(html_list[0])
        catalog_tree = html.fromstring(html_list[1])

        book_name = self._first_str(info_tree.xpath('//h1[@class="page-title"]/text()'))
        author = self._first_str(
            info_tree.xpath('//a[contains(@href,"/author/")]/@title')
        )
        cover_url = self._first_str(
            info_tree.xpath('//div[@class="novel-cover"]//img/@data-src')
        )
        serial_status = self._first_str(
            info_tree.xpath(
                '//a[@class="tag-link" and (text()="完结" or text()="连载")]/text()'
            )
        )
        word_count = self._first_str(
            info_tree.xpath('//span[contains(text(), "字")]/text()')
        )

        summary_node = info_tree.xpath(
            '//div[@class="novel-info-item novel-info-content"]/span'
        )
        if summary_node and summary_node[0] is not None:
            summary = str(summary_node[0].text_content()).strip()
        else:
            summary = ""

        update_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        volumes: list[VolumeInfoDict] = []
        current_volume: VolumeInfoDict | None = None

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

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "word_count": word_count,
            "serial_status": serial_status,
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

        # Content paragraphs
        paras = tree.xpath('//div[@class="article-content"]/p/text()')
        content_text = "\n".join(p.strip() for p in paras if p.strip())
        if not content_text:
            return None

        title_text = self._first_str(tree.xpath('//h1[@class="article-title"]/text()'))
        volume_text = self._first_str(tree.xpath('//h3[@class="text-muted"]/text()'))

        next_href = self._first_str(
            tree.xpath('//div[@class="footer"]/a[@class="f-right"]/@href')
        )
        next_cid = next_href.split("/")[-1].replace(".html", "") if next_href else ""

        return {
            "id": chapter_id,
            "title": title_text,
            "content": content_text,
            "extra": {
                "site": self.site_name,
                "volume": volume_text,
                "next_cid": next_cid,
            },
        }
