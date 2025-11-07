#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n17k.parser
------------------------------------------
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
class N17kParser(BaseParser):
    """
    Parser for 17K小说网 book pages.
    """

    site_name: str = "n17k"

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
            info_tree.xpath('//div[@class="Info Sign"]//h1/a/text()')
        )
        author = self._first_str(catalog_tree.xpath('//div[@class="Author"]/a/text()'))
        cover_url = self._first_str(info_tree.xpath('//div[@id="bookCover"]//img/@src'))
        serial_status = self._first_str(
            info_tree.xpath('//div[@class="label"]//span/text()')
        )
        word_count = self._first_str(
            info_tree.xpath('//div[@class="BookData"]/p/em[@class="red"]/text()')
        )
        update_time = self._first_str(
            info_tree.xpath('//dl[@id="bookInfo"]//em/text()'),
            replaces=[("更新:", "")],
        )

        tags = [
            tag.strip()
            for tag in info_tree.xpath('//tr[@class="label"]//span/text()')
            if tag.strip()
        ]

        summary = self._join_strs(
            info_tree.xpath('//p[@class="intro"]//text()'),
        )

        # --- Volumes & Chapters ---
        volumes: list[VolumeInfoDict] = []
        vol_idx: int = 1

        for vol in catalog_tree.xpath('//dl[@class="Volume"]'):
            vol_name = self._first_str(vol.xpath('./dt/span[@class="tit"]/text()'))

            vol_chaps: list[ChapterInfoDict] = []
            for a in vol.xpath("./dd/a"):
                href = a.get("href", "").strip()
                if not href:
                    continue

                span_elem = spans[0] if (spans := a.xpath(".//span")) else None

                if span_elem is not None:
                    title = span_elem.text_content().strip()
                    span_class = span_elem.get("class", "")
                else:
                    title = ""
                    span_class = ""

                accessible = "vip" not in span_class
                chapter_id = href.rsplit("/", 1)[-1].split(".", 1)[0]

                vol_chaps.append(
                    {
                        "title": title,
                        "url": href,
                        "chapterId": chapter_id,
                        "accessible": accessible,
                    }
                )

            if vol_chaps:
                volumes.append(
                    {
                        "volume_name": vol_name or f"未命名卷 {vol_idx}",
                        "chapters": vol_chaps,
                    }
                )
                vol_idx += 1

        if not volumes:
            return None

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "serial_status": serial_status,
            "word_count": word_count,
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
        if "VIP章节, 余下还有" in html_list[0]:
            return None

        tree = html.fromstring(html_list[0])

        # Content paragraphs
        paragraphs = [
            text
            for p in tree.xpath(
                '//div[@id="readArea"]//div[@class="p"]/p[not(@class)]/text()'
            )
            if (text := p.strip())
        ]

        if not paragraphs:
            return None

        content = "\n".join(paragraphs)
        author_say = self._join_strs(
            tree.xpath('//div[contains(@class,"author-say")]//text()')
        )

        title = self._first_str(tree.xpath('//div[@id="readArea"]//h1/text()'))
        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {
                "site": self.site_name,
                "author_say": author_say,
            },
        }
