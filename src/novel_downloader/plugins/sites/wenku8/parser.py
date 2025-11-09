#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.wenku8.parser
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
    VolumeInfoDict,
)


@registrar.register_parser()
class Wenku8Parser(BaseParser):
    """
    Parser for 轻小说文库 book-info pages.
    """

    site_name: str = "wenku8"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if len(html_list) < 2:
            return None

        info_tree = html.fromstring(html_list[0])
        catalog_tree = html.fromstring(html_list[1])

        # --- Metadata ---
        book_name = self._first_str(info_tree.xpath("//table//b/text()"))
        author = self._first_str(
            info_tree.xpath('//td[contains(text(),"小说作者")]/text()'),
            replaces=[("小说作者：", "")],
        )
        cover_url = self._first_str(
            info_tree.xpath('//img[contains(@src,"/image/")]/@src')
        )

        serial_status = self._first_str(
            info_tree.xpath('//td[contains(text(),"文章状态")]/text()'),
            replaces=[("文章状态：", "")],
        )
        word_count = self._first_str(
            info_tree.xpath('//td[contains(text(),"全文长度")]/text()'),
            replaces=[("全文长度：", "")],
        )
        update_time = self._first_str(
            info_tree.xpath('//td[contains(text(),"最后更新")]/text()'),
            replaces=[("最后更新：", "")],
        )

        tags_text = self._first_str(
            info_tree.xpath('//span[contains(text(),"Tags")]/b/text()')
        )
        if tags_text:
            tags_text = tags_text.replace("作品Tags：", "").replace("　", " ")
            tags: list[str] = [t.strip() for t in tags_text.split() if t.strip()]
        else:
            tags = []

        summary = self._join_strs(
            info_tree.xpath(
                '//span[contains(text(),"内容简介")]/following-sibling::span[1]//text()'
            )
        )

        # --- Volumes & Chapters ---
        volumes: list[VolumeInfoDict] = []
        vol_idx: int = 1
        vol_name: str | None = None
        vol_chaps: list[ChapterInfoDict] = []

        def flush_volume() -> None:
            nonlocal vol_idx, vol_name, vol_chaps
            if not vol_chaps:
                return
            volumes.append(
                {
                    "volume_name": vol_name or f"未命名卷 {vol_idx}",
                    "chapters": vol_chaps,
                }
            )
            vol_idx += 1
            vol_name = None
            vol_chaps = []

        # Parse catalog table
        for elem in catalog_tree.xpath('//table[@class="css"]//tr'):
            td_v = elem.xpath('./td[@class="vcss"]/text()')
            if td_v:
                # new volume
                flush_volume()
                vol_name = td_v[0].strip()
                continue

            for a in elem.xpath('.//td[@class="ccss"]/a'):
                href = a.get("href", "").strip()
                if not href:
                    continue
                title = a.text_content().strip()
                chapter_id = href.split(".")[0]
                vol_chaps.append(
                    {
                        "title": title,
                        "url": href,
                        "chapterId": chapter_id,
                    }
                )

        flush_volume()

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

    def parse_chapter(
        self,
        html_list: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        if not html_list:
            return None

        tree = html.fromstring(html_list[0])
        title = self._first_str(tree.xpath('//div[@id="title"]/text()'))

        paragraphs: list[str] = []
        image_positions: dict[int, list[dict[str, Any]]] = {}
        image_idx = 0

        # Iterate through direct children of content div
        for elem in tree.xpath('//div[@id="content"]/*'):
            tag = (elem.tag or "").lower()

            # Skip site footers or ads
            if tag == "ul" and elem.get("id") == "contentdp":
                # include tail (might have text after ul)
                if tail := (elem.tail or "").strip():
                    paragraphs.append(tail)
                    image_idx += 1
                continue

            elif tag == "div" and "divimage" in (elem.get("class") or ""):
                # Collect all image links
                urls = elem.xpath(".//a/@href") or elem.xpath(".//img/@src")
                for src in urls:
                    src = src.strip()
                    if not src:
                        continue
                    # normalize URL
                    if src.startswith("//"):
                        src = "https:" + src
                    # elif src.startswith("/"):
                    #     src = self.BASE_URL + src
                    image_positions.setdefault(image_idx, []).append(
                        {
                            "type": "url",
                            "data": src,
                        }
                    )
                if tail := (elem.tail or "").strip():
                    paragraphs.append(tail)
                    image_idx += 1
                continue

            elif tag == "br":
                if tail := (elem.tail or "").strip():
                    paragraphs.append(tail)
                    image_idx += 1
                continue

            else:
                if text := elem.text_content().strip():
                    paragraphs.append(text)
                    image_idx += 1
                if tail := (elem.tail or "").strip():
                    paragraphs.append(tail)
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
