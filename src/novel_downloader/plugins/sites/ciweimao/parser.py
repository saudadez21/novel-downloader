#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ciweimao.parser
----------------------------------------------
"""

import logging
from typing import Any

from lxml import html
from novel_downloader.plugins.base.parser import BaseParser
from novel_downloader.plugins.registry import registrar
from novel_downloader.plugins.utils.ciweimao import CiweimaoChapterMixin
from novel_downloader.schemas import (
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    MediaResource,
    VolumeInfoDict,
)

logger = logging.getLogger(__name__)


@registrar.register_parser()
class CiweimaoParser(CiweimaoChapterMixin, BaseParser):
    """
    Parser for 刺猬猫 book pages.
    """

    site_name: str = "ciweimao"

    def parse_book_info(
        self,
        raw_pages: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if len(raw_pages) < 2:
            return None

        # Parse trees
        info_tree = html.fromstring(raw_pages[0])
        catalog_tree = html.fromstring(raw_pages[1])

        book_name = self._first_str(
            info_tree.xpath('//meta[@property="og:novel:book_name"]/@content')
        )
        if not book_name:
            book_name = self._first_str(info_tree.xpath('//h1[@class="title"]/text()'))

        author = self._first_str(
            info_tree.xpath('//meta[@property="og:novel:author"]/@content')
        )
        if not author:
            author = self._first_str(
                info_tree.xpath('//h1[@class="title"]/span/a/text()')
            )

        cover_url = self._first_str(
            info_tree.xpath('//meta[@property="og:image"]/@content')
        )
        if not cover_url:
            cover_url = self._first_str(
                info_tree.xpath('//div[@class="cover"]//img/@src')
            )

        update_time = self._first_str(
            info_tree.xpath('//p[@class="update-time"]/text()'),
            replaces=[("最后更新：", "")],
        )

        word_count = self._first_str(
            info_tree.xpath('//p[@class="book-grade"]/b[last()]/text()')
        )

        serial_status = self._first_str(
            info_tree.xpath('//p[@class="update-state"]/text()')
        )

        tags: list[str] = [
            t.strip()
            for t in info_tree.xpath(
                '//p[@class="label-box"]//span[contains(@class,"label-warning")]//a/text()'
            )
            if t.strip()
        ]

        cat_val = self._first_str(
            info_tree.xpath('//meta[@property="og:novel:category"]/@content')
        )
        if cat_val and cat_val not in tags:
            tags.append(cat_val)

        summary = self._first_str(
            info_tree.xpath('//meta[@property="og:description"]/@content')
        )
        if not summary:
            texts = info_tree.xpath('//div[contains(@class,"book-desc")]//text()')
            summary = self._join_strs(texts, replaces=[("\xa0", ""), ("\u3000", "")])

        # --- Volumes & Chapters ---
        volumes: list[VolumeInfoDict] = []
        vol_idx: int = 1

        for vol in catalog_tree.xpath('//div[contains(@class,"book-chapter-box")]'):
            elems = vol.xpath('.//h4[contains(@class,"sub-tit")]')
            vol_name = elems[0].text_content().strip() if elems else ""
            vol_name = vol_name or f"未命名卷 {vol_idx}"

            # chapter list
            chapters: list[ChapterInfoDict] = []
            for a in vol.xpath('.//ul[contains(@class,"book-chapter-list")]//a'):
                href = a.get("href", "").strip()
                if not href:
                    continue

                chapter_id = href.strip("/").rsplit("/", 1)[-1]
                title = a.text_content().strip()

                # accessibility: locked if contains icon-lock
                accessible = not bool(a.xpath('.//i[contains(@class,"icon-lock")]'))

                chapters.append(
                    {
                        "title": title,
                        "url": href,
                        "chapterId": chapter_id,
                        "accessible": accessible,
                    }
                )

            volumes.append(
                {
                    "volume_name": vol_name,
                    "chapters": chapters,
                }
            )

        if not volumes:
            return None

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "word_count": word_count,
            "serial_status": serial_status,
            "tags": tags,
            "summary": summary,
            "volumes": volumes,
            "extra": {},
        }

    def parse_chapter_content(
        self,
        raw_pages: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        if len(raw_pages) < 3:
            return None

        html_page = raw_pages[0]
        is_image_chapter = "J_ImgRead" in html_page

        paragraphs: list[str] = []
        resources: list[MediaResource] = []

        tree = html.fromstring(html_page)
        title = self._first_str(
            tree.xpath(
                '//div[@id="J_BookCnt"]'
                '//div[contains(@class,"read-hd")]'
                '//h1[contains(@class,"chapter")]/text()'
            )
        )
        author_say = self._join_strs(
            tree.xpath(
                '//div[@id="J_BookCnt"]//p[contains(@class,"author_say")]//text()'
            )
        )

        if is_image_chapter:
            img_b64 = raw_pages[1].strip()
            tsukkomi_list_str = raw_pages[2]

            paragraphs, resources = self._parse_image_chapter(
                img_b64, tsukkomi_list_str
            )
        else:
            detail_json_str = raw_pages[1]
            session_json_str = raw_pages[2]
            paragraphs, resources = self._parse_text_chapter(
                detail_json_str, session_json_str
            )

        if not (paragraphs or resources):
            return None

        content = "\n".join(paragraphs)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {
                "site": self.site_name,
                "image_chapter": is_image_chapter,
                "author_say": author_say,
                "resources": resources,
            },
        }
