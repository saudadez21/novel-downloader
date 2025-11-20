#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ciweimao.parser
----------------------------------------------
"""

import base64
import json
import logging
from typing import Any

from lxml import html
from novel_downloader.libs.fontocr import get_font_ocr
from novel_downloader.plugins.base.parser import BaseParser
from novel_downloader.plugins.registry import registrar
from novel_downloader.plugins.utils.ciweimao.my_encryt import my_decrypt
from novel_downloader.schemas import (
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    MediaResource,
    VolumeInfoDict,
)

logger = logging.getLogger(__name__)


@registrar.register_parser()
class CiweimaoParser(BaseParser):
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
            vol_name = self._first_str(vol.xpath('.//h4[contains(@class,"sub-tit")]'))
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

            if self._enable_ocr:
                paragraphs, resources = self._parse_image_chapter(
                    img_b64, tsukkomi_list_str
                )
            else:
                resources.append(
                    {
                        "type": "image",
                        "paragraph_index": 0,
                        "base64": img_b64,
                        "mime": "image/jpeg",
                    }
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

    def _parse_text_chapter(
        self,
        detail_json_str: str,
        session_json_str: str,
    ) -> tuple[list[str], list[MediaResource]]:
        """
        Returns: (paragraphs, resources, title, author_say)
        """
        detail_obj = json.loads(detail_json_str)
        session_obj = json.loads(session_json_str)

        # structure from JS: chapter_content, encryt_keys, rad
        enc_content = detail_obj.get("chapter_content")
        enc_keys = detail_obj.get("encryt_keys") or []
        access_key = session_obj.get("chapter_access_key")

        if not enc_content or not enc_keys or not access_key:
            logger.warning(
                "Missing encryption fields in detail/session JSON: %s / %s",
                detail_obj,
                session_obj,
            )
            return [], []

        decrypted_html = my_decrypt(
            content=enc_content,
            keys=enc_keys,
            access_key=access_key,
        )

        # wrap into a root so lxml sees valid XML
        root = html.fromstring(f"<root>{decrypted_html}</root>")

        # remove all span elements (like <span>abcde</span>)
        for span in root.xpath(".//span"):
            parent = span.getparent()
            if parent is not None:
                parent.remove(span)

        resources: list[MediaResource] = []
        paragraphs: list[str] = []
        curr_paragraph_idx = 0

        for p_elem in root.xpath(".//p"):
            # collect images in this paragraph
            for img_elem in p_elem.xpath(".//img"):
                src = (img_elem.get("src") or "").strip()
                if not src:
                    continue
                if src.startswith("//"):
                    src = "https:" + src

                alt = img_elem.get("alt") or ""

                resources.append(
                    {
                        "type": "image",
                        "paragraph_index": curr_paragraph_idx,
                        "url": src,
                        "alt": alt,
                    }
                )

            text_content = p_elem.text_content().strip()
            if text_content:
                paragraphs.append(text_content)
                curr_paragraph_idx += 1

        return paragraphs, resources

    def _parse_image_chapter(
        self,
        img_base64: str,
        tsukkomi_list_json_str: str,
    ) -> tuple[list[str], list[MediaResource]]:
        ocr = get_font_ocr(self._fontocr_cfg)
        if not ocr:
            logger.warning("fail to load OCR")
            return [], []

        from novel_downloader.plugins.utils.ciweimao.image import split_image

        paragraphs: list[str] = []
        resources: list[MediaResource] = []
        current_paragraph_no: int = 0

        # decode & preprocess
        image_tsukkomi_list = json.loads(tsukkomi_list_json_str)
        img_bytes = base64.b64decode(img_base64)
        img_arr = ocr.load_image_array_bytes(img_bytes)

        result = split_image(img_arr, image_tsukkomi_list)

        ocr_outputs = ocr.predict(result.images, batch_size=self._batch_size)

        for blk in result.blocks:
            if blk["type"] == "image":
                resources.append(
                    {
                        "type": "image",
                        "paragraph_index": current_paragraph_no,
                        "url": blk["url"],
                    }
                )
            elif blk["type"] == "paragraph":
                para_text = [ocr_outputs[i][0].strip() for i in blk["image_idxs"]]
                paragraphs.append("".join(para_text))
                current_paragraph_no += 1

        return paragraphs, resources
