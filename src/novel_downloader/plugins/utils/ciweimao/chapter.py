#!/usr/bin/env python3
"""
novel_downloader.plugins.utils.ciweimao.chapter
-----------------------------------------------
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
    import numpy as np
    from numpy.typing import NDArray

    from novel_downloader.plugins.protocols.parser import _ParserContext

    class CiweimaoChapterContext(_ParserContext, Protocol):
        """"""

        _CHAPTER_BACKGROUND: tuple[int, int, int]
        _PAGE_LINE_LIMIT: int


class CiweimaoChapterMixin:
    """Ciweimao chapter parser mixin."""

    _CHAPTER_BACKGROUND: tuple[int, int, int] = (255, 255, 255)
    _PAGE_LINE_LIMIT: int = 15

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
        try:
            if not self._enable_ocr and self._cut_mode == "none":
                return [], [
                    {
                        "type": "image",
                        "paragraph_index": 0,
                        "base64": img_base64,
                        "mime": "image/jpeg",
                    }
                ]

            from novel_downloader.libs import imagekit

            from .image import split_image

            # decode & preprocess
            tsukkomi_list = json.loads(tsukkomi_list_json_str)
            img_bytes = base64.b64decode(img_base64)
            img_arr = imagekit.load_image_array_bytes(img_bytes)

            result = split_image(
                img_arr,
                tsukkomi_list,
                background=self._CHAPTER_BACKGROUND,
                remove_watermark=self._remove_watermark,
            )

            if self._enable_ocr:
                paragraphs: list[str] = []
                resources: list[MediaResource] = []
                current_paragraph_no: int = 0

                try:
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
                            para_text = [
                                ocr_outputs[i][0].strip() for i in blk["image_idxs"]
                            ]
                            paragraphs.append("".join(para_text))
                            current_paragraph_no += 1

                    return paragraphs, resources
                except Exception as e:
                    logger.warning(
                        "OCR failed, falling back to image slicing mode.",
                        exc_info=e,
                    )

            if self._cut_mode == "paragraph":
                resources = []
                for blk in result.blocks:
                    if blk["type"] == "image":
                        resources.append(
                            {
                                "type": "image",
                                "paragraph_index": 0,
                                "url": blk["url"],
                            }
                        )
                    elif blk["type"] == "paragraph":
                        para_slices = [result.images[i] for i in blk["image_idxs"]]
                        img_bytes = imagekit.concat_image_slices_vertical(
                            para_slices, format="JPEG"
                        )
                        resources.append(
                            {
                                "type": "image",
                                "paragraph_index": 0,
                                "base64": base64.b64encode(img_bytes).decode("ascii"),
                                "mime": "image/jpeg",
                            }
                        )

                return [], resources

            resources = []
            page_buffer: "list[NDArray[np.uint8]]" = []
            page_line_count = 0

            def flush_page() -> None:
                nonlocal page_buffer, page_line_count

                if not page_buffer:
                    return

                img_bytes = imagekit.concat_image_slices_vertical(
                    page_buffer, format="JPEG"
                )

                resources.append(
                    {
                        "type": "image",
                        "paragraph_index": 0,
                        "base64": base64.b64encode(img_bytes).decode("ascii"),
                        "mime": "image/jpeg",
                    }
                )

                # reset
                page_buffer = []
                page_line_count = 0

            for blk in result.blocks:
                if blk["type"] == "image":
                    flush_page()
                    resources.append(
                        {
                            "type": "image",
                            "paragraph_index": 0,
                            "url": blk["url"],
                        }
                    )
                    continue

                elif blk["type"] == "paragraph":
                    for idx in blk["image_idxs"]:
                        slc = result.images[idx]
                        if page_line_count >= self._PAGE_LINE_LIMIT:
                            flush_page()
                        page_buffer.append(slc)
                        page_line_count += 1
                    continue

            flush_page()

            return [], resources

        except Exception as e:
            logger.warning("Unexpected error in image chapter parsing.", exc_info=e)

        return [], [
            {
                "type": "image",
                "paragraph_index": 0,
                "base64": img_base64,
                "mime": "image/jpeg",
            }
        ]
