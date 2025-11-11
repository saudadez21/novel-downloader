#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.linovel.parser
---------------------------------------------
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
class LinovelParser(BaseParser):
    """
    Parser for 轻之文库 book pages.
    """

    site_name: str = "linovel"
    BASE_URL = "https://lnovel.org"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        # core fields
        book_name = self._first_str(
            tree.xpath('//meta[@property="og:title"]/@content')
            or tree.xpath('//h1[contains(@class,"book-title")]/text()')
        )

        cover_url = self._first_str(
            tree.xpath('//meta[@property="og:image"]/@content')
            or tree.xpath('//div[contains(@class,"book-cover")]//img/@src')
            or tree.xpath('//div[contains(@class,"book-cover")]//a/@href')
        )

        author = self._first_str(
            tree.xpath(
                '//div[contains(@class,"sidebar")]//div[contains(@class,"novelist")]//div[contains(@class,"name")]//a/text()'
            )
        )

        update_time = self._first_str(
            tree.xpath('//div[contains(@class,"book-last-update")]/text()'),
            replaces=[("更新于", ""), ("\xa0", " ")],
        )

        serial_status = self._first_str(
            tree.xpath(
                '(//div[contains(@class,"book-data")]//span[not(contains(@class,"hint"))]/text())[last()]'
            )
        )

        tags = [
            t.strip()
            for t in tree.xpath('//div[contains(@class,"book-cats")]//a/text()')
            if t and t.strip()
        ]

        summary = self._join_strs(
            tree.xpath(
                '//div[contains(@class,"section") and contains(@class,"introduction")]//div[contains(@class,"about-text")]//text()'  # noqa: E501
            ),
            replaces=[("\xa0", " ")],
        )

        # volumes & chapters
        volumes: list[VolumeInfoDict] = []
        section_nodes = tree.xpath(
            '//div[contains(@class,"section-list")]//div[contains(@class,"section") and @data-index-name]'  # noqa: E501
        )
        for sec in section_nodes:
            volume_name = self._first_str(
                sec.xpath('.//h2[contains(@class,"volume-title")]//text()')
            )

            volume_cover = self._first_str(
                sec.xpath('.//div[contains(@class,"volume-cover")]//img/@src')
                or sec.xpath('.//div[contains(@class,"volume-cover")]//a/@href')
            )

            volume_intro = self._join_strs(
                sec.xpath(
                    './/div[contains(@class,"volume-desc-wrp")]//div[contains(@class,"text-content-actual")]//text()'
                ),
                replaces=[("\xa0", " ")],
            )

            volume_hint = self._first_str(
                sec.xpath('.//div[contains(@class,"volume-hint")]/text()')
            )

            chapters: list[ChapterInfoDict] = []
            for a in sec.xpath('.//div[contains(@class,"chapter-list")]//a'):
                ch_url = a.get("href", "").strip()
                if not ch_url or ch_url.startswith("javascript:"):
                    continue

                ch_title = self._first_str([a.text_content()])
                ch_id = ch_url.rsplit("/", 1)[-1].split(".", 1)[0]

                chapters.append(
                    {
                        "title": ch_title,
                        "url": ch_url,
                        "chapterId": ch_id,
                    }
                )

            vol: VolumeInfoDict = {
                "volume_name": volume_name,
                "chapters": chapters,
            }
            if volume_cover:
                vol["volume_cover"] = volume_cover
            if volume_hint:
                vol["word_count"] = volume_hint
            if volume_intro:
                vol["volume_intro"] = volume_intro

            volumes.append(vol)

        if not volumes:
            return None

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
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])

        title = self._first_str(
            tree.xpath('//div[contains(@class,"article-title")]/text()')
        )

        paragraphs: list[str] = []
        image_positions: dict[int, list[dict[str, Any]]] = {}
        image_idx = 0

        for p in tree.xpath(
            '//div[contains(@class,"article-text")]//p[contains(@class,"l")]'
        ):
            classes = p.get("class") or ""

            if "l-image" in classes:
                urls = [u.strip() for u in p.xpath(".//a/@href") if u and u.strip()]
                if not urls:
                    urls = [
                        u.strip() for u in p.xpath(".//img/@src") if u and u.strip()
                    ]
                if not urls:
                    continue

                img_objs: list[dict[str, Any]] = []
                for url in urls:
                    if url.startswith("//"):
                        url = "https:" + url
                    img_objs.append({"type": "url", "data": url})

                image_positions.setdefault(image_idx, []).extend(img_objs)
            else:
                txt = p.text_content().replace("\xa0", " ").strip()
                if txt:
                    paragraphs.append(txt)
                    image_idx += 1

        if not (paragraphs or image_positions):
            return None

        content = "\n".join(paragraphs)

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {
                "site": self.site_name,
                "image_positions": image_positions,
            },
        }
