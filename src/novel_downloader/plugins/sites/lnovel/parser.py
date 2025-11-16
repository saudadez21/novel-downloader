#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.lnovel.parser
--------------------------------------------

"""

from typing import Any

from lxml import html
from novel_downloader.plugins.base.parser import BaseParser
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import (
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    MediaResource,
    VolumeInfoDict,
)


@registrar.register_parser()
class LnovelParser(BaseParser):
    """
    Parser for 轻小说百科 book pages.
    """

    site_name: str = "lnovel"
    BASE_URL = "https://lnovel.org"

    def parse_book_info(
        self,
        raw_pages: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if not raw_pages:
            return None

        tree = html.fromstring(raw_pages[0])

        book_name = self._first_str(tree.xpath("//main//h1/text()"))
        author = self._first_str(
            tree.xpath(
                '//dt[contains(normalize-space(.), "作者")]/following-sibling::dd[1]//a/text()'  # noqa: E501
            )
        )
        cover_url = self.BASE_URL + self._first_str(
            tree.xpath('//meta[@property="og:image"]/@content')
        )

        update_time = self._first_str(
            tree.xpath(
                '//dt[contains(normalize-space(.), "更新")]/following-sibling::dd[1]/text()'  # noqa: E501
            )
        )
        serial_status = self._first_str(
            tree.xpath(
                '//dt[contains(normalize-space(.), "状态")]/following-sibling::dd[1]//a/text()'  # noqa: E501
            )
        )

        paras = tree.xpath(
            '//h2[contains(.,"简介")]/following-sibling::p[contains(@class,"my-2")]'
        )
        summary = "\n".join(
            text for p in paras if (text := "".join(p.xpath(".//text()")).strip())
        )
        if not summary:
            summary = self._first_str(
                tree.xpath('//meta[@name="description"]/@content')
            )

        tags = [
            t.strip()
            for t in tree.xpath(
                '//dt[contains(normalize-space(.), "类别")]/following-sibling::dd[1]//a/text()'  # noqa: E501
            )
            if t and t.strip()
        ]

        # volumes & chapters
        volumes: list[VolumeInfoDict] = []
        for item in tree.xpath(
            '//div[@id="volumes"]/div[contains(@class, "accordion-item")]'
        ):
            volume_name = self._first_str(
                item.xpath('.//a[contains(@class, "accordion-button")]/text()')
            )
            chapters: list[ChapterInfoDict] = []
            for a in item.xpath('.//div[contains(@class, "list-group")]//a[@href]'):
                url = (a.get("href") or "").strip()
                title = self._first_str(a.xpath(".//text()"))
                chapter_id = url.rsplit("-", 1)[-1] if "-" in url else url
                chapters.append(
                    {
                        "title": title,
                        "url": url,
                        "chapterId": chapter_id,
                    }
                )
            volumes.append({"volume_name": volume_name, "chapters": chapters})

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

    def parse_chapter_content(
        self,
        raw_pages: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        if not raw_pages:
            return None

        tree = html.fromstring(raw_pages[0])

        vol_name = self._first_str(
            tree.xpath('//article//div[contains(@class,"card-header")]/text()')
        )

        title = self._first_str(tree.xpath("//main//h1/text()"))

        paragraphs: list[str] = []
        resources: list[MediaResource] = []
        curr_paragraph_idx = 0

        for idx, elem in enumerate(tree.xpath('//*[@id="chaptersShowContent"]/*')):
            tag = elem.tag.lower()

            if tag == "p":
                txt = "".join(elem.xpath(".//text()")).strip()
                if idx < 2 and txt:
                    txt = txt.replace(title, "").replace(vol_name, "").strip()
                if txt:
                    paragraphs.append(txt)
                    curr_paragraph_idx += 1

            elif tag == "img":
                src = (elem.get("src") or "").strip()
                if src.startswith("/"):
                    src = self.BASE_URL + src

                if src:
                    resources.append(
                        {
                            "type": "image",
                            "paragraph_index": curr_paragraph_idx,
                            "url": src,
                        }
                    )

        # image gallery right after content block
        for src in tree.xpath(
            '//*[@id="chaptersShowContent"]/following-sibling::a[img]//img/@src'
        ):
            src = (src or "").strip()
            if src.startswith("/"):
                src = self.BASE_URL + src

            if src:
                resources.append(
                    {
                        "type": "image",
                        "paragraph_index": curr_paragraph_idx,
                        "url": src,
                    }
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
                "resources": resources,
            },
        }
