#!/usr/bin/env python3
"""
novel_downloader.plugins.processors.zh_convert
----------------------------------------------

Converts Chinese text between 简体 <-> 繁体 using pycorrector utilities.
"""

from __future__ import annotations

import copy
from collections.abc import Callable
from typing import Any

from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import BookInfoDict, ChapterDict

_ALLOWED_DIRECTIONS = {
    "hk2s",
    "s2hk",
    "s2t",
    "s2tw",
    "s2twp",
    "t2hk",
    "t2s",
    "t2tw",
    "tw2s",
    "tw2sp",
}


@registrar.register_processor()
class ZhConvertProcessor:
    """
    简繁转换处理器 (Simplified/Traditional Chinese conversion via OpenCC)
    """

    def __init__(self, config: dict[str, Any]) -> None:
        self._apply_title = bool(config.get("apply_title", True))
        self._apply_content = bool(config.get("apply_content", True))
        self._apply_author = bool(config.get("apply_author", False))
        self._apply_tags = bool(config.get("apply_tags", False))

        direction = (config.get("direction") or "t2s").lower()
        self._convert = self._build_converter(direction)

    def process_book_info(self, book_info: BookInfoDict) -> BookInfoDict:
        bi = copy.deepcopy(book_info)

        # Title-like
        if self._apply_title and isinstance(name := bi.get("book_name"), str):
            bi["book_name"] = self._convert_text(name)
        if self._apply_author and isinstance(author := bi.get("author"), str):
            bi["author"] = self._convert_text(author)

        # Content-like
        if self._apply_content and isinstance(summary := bi.get("summary"), str):
            bi["summary"] = self._convert_text(summary)

        # Tags
        if self._apply_tags and isinstance(tags := bi.get("tags"), list):
            bi["tags"] = [
                self._convert_text(t) if isinstance(t, str) else t for t in tags
            ]

        # Volumes & chapters
        if isinstance(volumes := bi.get("volumes"), list):
            for vol in volumes:
                if self._apply_title and isinstance(
                    vname := vol.get("volume_name"), str
                ):
                    vol["volume_name"] = self._convert_text(vname)

                if self._apply_content and isinstance(
                    intro := vol.get("volume_intro"), str
                ):
                    vol["volume_intro"] = self._convert_text(intro)

                if isinstance(chapters := vol.get("chapters"), list):
                    for cinfo in chapters:
                        if self._apply_title and isinstance(
                            ctitle := cinfo.get("title"), str
                        ):
                            cinfo["title"] = self._convert_text(ctitle)

        return bi

    def process_chapter(self, chapter: ChapterDict) -> ChapterDict:
        ch = copy.deepcopy(chapter)

        if self._apply_title and isinstance(title := ch.get("title"), str):
            ch["title"] = self._convert_text(title)
        if self._apply_content and isinstance(content := ch.get("content"), str):
            ch["content"] = self._convert_text(content)

        return ch

    def _build_converter(self, direction: str) -> Callable[[str], str]:
        """
        Build the pycorrector converter based on direction.
        """
        if direction not in _ALLOWED_DIRECTIONS:
            raise ValueError(
                f"direction must be one of {_ALLOWED_DIRECTIONS}, got: {direction}"
            )

        try:
            from opencc import OpenCC
        except Exception as e:
            raise ImportError(
                "ZhConvertProcessor requires OpenCC. Install with:\n"
                "  pip install opencc-python-reimplemented"
            ) from e

        return OpenCC(direction).convert  # type: ignore[no-any-return]

    def _convert_text(self, text: str) -> str:
        if not isinstance(text, str) or not text:
            return text

        return self._convert(text)
