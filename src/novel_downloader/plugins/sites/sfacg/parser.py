#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.sfacg.parser
-------------------------------------------

"""

import base64
import logging
from typing import Any

from lxml import html

from novel_downloader.infra.fontocr import get_font_ocr
from novel_downloader.plugins.base.parser import BaseParser
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import (
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    VolumeInfoDict,
)

logger = logging.getLogger(__name__)


@registrar.register_parser()
class SfacgParser(BaseParser):
    """
    Parser for sfacg book pages.
    """

    site_name: str = "sfacg"

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        if len(html_list) < 2:
            return None

        info_tree = html.fromstring(html_list[0])
        catalog_tree = html.fromstring(html_list[1])

        # Book metadata
        book_name = self._first_str(
            info_tree.xpath('//span[@class="book_newtitle"]/text()')
        )

        book_info2 = info_tree.xpath('//div[@class="book_info2"]/span/text()')
        book_type = self._first_str(book_info2[0:1])
        serial_status = self._first_str(book_info2[1:2])

        # author / word_count / update_time
        book_info3_nodes = info_tree.xpath('//span[@class="book_info3"]//text()')
        author, word_count, update_time = "", "", ""
        if book_info3_nodes:
            # first part "author / word_count / skipped"
            parts = [p.strip() for p in book_info3_nodes[0].split("/") if p.strip()]
            if len(parts) >= 2:
                author = parts[0]
                word_count = parts[1]  # keep with "字"
            if len(book_info3_nodes) >= 2:
                update_time = book_info3_nodes[-1].strip()

        cover_url = "https:" + self._first_str(
            info_tree.xpath('//ul[@class="book_info"]//img/@src')
        )

        summary = self._join_strs(
            info_tree.xpath(
                '//ul[@class="book_profile"]/li[@class="book_bk_qs1"]//text()'
            )
        )

        # --- catalog parsing ---
        volumes: list[VolumeInfoDict] = []
        vol_nodes = catalog_tree.xpath('//div[@class="mulu"]')
        for vol_node in vol_nodes:
            vol_name = vol_node.text_content().strip()
            ul = vol_node.getnext()
            chapters: list[ChapterInfoDict] = []
            if ul is not None:
                for a in ul.xpath('.//ul[@class="mulu_list"]/a'):
                    url = self._first_str(a.xpath("./@href"))
                    if not url:
                        continue
                    chapter_id = url.strip("/").rsplit("/", 1)[-1]
                    title_texts = a.xpath(".//li//text()")
                    title = self._join_strs(title_texts)

                    chap: ChapterInfoDict = {
                        "title": title,
                        "url": url,
                        "chapterId": chapter_id,
                    }
                    chapters.append(chap)
            volumes.append(
                {
                    "volume_name": vol_name,
                    "chapters": chapters,
                }
            )

        return {
            "book_name": book_name,
            "author": author,
            "cover_url": cover_url,
            "update_time": update_time,
            "word_count": word_count,
            "serial_status": serial_status,
            "summary": summary,
            "tags": [book_type] if book_type else [],
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

        # check if chapter is locked
        keywords = ["本章为VIP章节"]  # 本章为VIP章节，订阅后可立即阅读
        if any(kw in html_list[0] for kw in keywords):
            return None

        tree = html.fromstring(html_list[0])
        content = ""

        is_vip = "/ajax/ashx/common.ashx" in html_list[0]

        # case: VIP chapter -> needs OCR from base64 image
        if is_vip:
            if not self._decode_font:
                logger.warning(
                    "sfacg chapter %s :: vip decryption skipped "
                    "(set `decode_font=True` to enable)",
                    chapter_id,
                )
                return None

            if len(html_list) < 2:
                logger.warning("sfacg chapter %s :: missing VIP img data", chapter_id)
                return None

            content = self.parse_vip_chapter(html_list[1])

        # case: normal HTML text chapter
        else:
            content_div = tree.xpath('//div[@class="yuedu Content_Frame"]/div[1]')
            if not content_div:
                logger.warning("sfacg chapter %s :: missing content div", chapter_id)
                return None

            content = self.parse_normal_chapter(content_div[0])

        if not content:
            return None

        title = self._first_str(
            tree.xpath('//ul[@class="menu_top_list book_view_top"]/li[2]/text()')
        )

        return {
            "id": chapter_id,
            "title": title,
            "content": content,
            "extra": {
                "site": self.site_name,
                "vip": is_vip,
            },
        }

    def parse_normal_chapter(self, content_div: html.HtmlElement) -> str:
        result = []
        for elem in content_div.iter():
            if elem.text and elem.tag not in ("img",):
                text = elem.text.strip()
                if text:
                    result.append(text)

            if elem.tag == "img":
                src = elem.get("src")
                if src:
                    result.append(f'<img src="{src}" />')

            if elem is content_div:
                continue
            if elem.tail and elem.tail.strip():
                result.append(elem.tail.strip())

        return "\n".join(result)

    def parse_vip_chapter(self, img_base64: str) -> str:
        ocr = get_font_ocr(self._fontocr_cfg)
        if not ocr:
            logger.warning("fail to load OCR")
            return ""

        img_bytes = base64.b64decode(img_base64)
        paragraphs: list[str] = []
        cache: list[str] = []

        # decode & preprocess
        img = ocr.gif_to_array_bytes(img_bytes)
        img = ocr.filter_orange_watermark(img)
        lines = ocr.split_by_height(
            img,
            height=38,
            top_offset=10,
            bottom_offset=10,
            per_chunk_top_ignore=10,
        )

        # filter out completely empty (white) lines
        non_empty_lines = [line for line in lines if not ocr.is_empty_image(line)]

        preds = ocr.predict(non_empty_lines, batch_size=32)
        for line, (text, _) in zip(non_empty_lines, preds, strict=False):
            first_2 = ocr.crop_chars_region(line, 2, left_margin=14, char_width=28)
            if ocr.is_empty_image(first_2) and cache:
                paragraphs.append("".join(cache))
                cache.clear()

            if text.strip():
                cache.append(text.strip())

        # flush cache
        if cache:
            paragraphs.append("".join(cache))

        return "\n".join(paragraphs)
