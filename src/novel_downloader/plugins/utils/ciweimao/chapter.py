#!/usr/bin/env python3
"""
novel_downloader.plugins.utils.ciweimao.image_chapter
-----------------------------------------------------
"""

import base64
import json
import logging
from typing import TYPE_CHECKING, Protocol

from lxml import html

from novel_downloader.schemas import MediaResource

from .my_encryt_extend import my_decrypt

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from novel_downloader.plugins.protocols.parser import _ParserContext

    class CiweimaoChapterContext(_ParserContext, Protocol):
        """"""


class CiweimaoChapterMixin:
    """Ciweimao chapter parser mixin."""

    def _parse_text_chapter(
        self: "CiweimaoChapterContext",
        detail_json_str: str,
        session_json_str: str,
    ) -> tuple[list[str], list[MediaResource]]:
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

        root = html.fromstring(decrypted_html)

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
        self: "CiweimaoChapterContext",
        img_base64: str,
        tsukkomi_list_json_str: str,
    ) -> tuple[list[str], list[MediaResource]]:
        from novel_downloader.libs import imagekit
        from novel_downloader.plugins.utils.ciweimao.image import split_image

        paragraphs: list[str] = []
        resources: list[MediaResource] = []
        current_paragraph_no: int = 0

        # decode & preprocess
        image_tsukkomi_list = json.loads(tsukkomi_list_json_str)
        img_bytes = base64.b64decode(img_base64)
        img_arr = imagekit.load_image_array_bytes(img_bytes)

        result = split_image(img_arr, image_tsukkomi_list)

        ocr_outputs = self._extract_text_from_image(
            result.images, batch_size=self._batch_size
        )

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
