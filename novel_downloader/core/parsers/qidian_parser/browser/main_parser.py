#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.parsers.qidian_parser.browser.main_parser
---------------------------------------------------------------

Main parser class for handling Qidian chapters rendered via a browser environment.

This module defines `QidianBrowserParser`, a parser implementation that supports
content extracted from dynamically rendered Qidian HTML pages.
"""

from pathlib import Path
from typing import Any, Dict, Optional

from novel_downloader.config.models import ParserConfig
from novel_downloader.core.parsers.base_parser import BaseParser

from ..shared import (
    is_encrypted,
    parse_book_info,
)
from .chapter_router import parse_chapter


class QidianBrowserParser(BaseParser):
    """
    Parser for Qidian site using a browser-rendered HTML workflow.
    """

    def __init__(self, config: ParserConfig):
        """
        Initialize the QidianBrowserParser with the given configuration.

        :param config: ParserConfig object controlling:
        """
        super().__init__(config)

        # Extract and store parser flags from config
        self._decode_font: bool = config.decode_font
        self._use_freq: bool = config.use_freq
        self._use_ocr: bool = config.use_ocr
        self._save_font_debug: bool = config.save_font_debug

        self._fixed_font_dir: Path = self._base_cache_dir / "fixed_fonts"
        self._fixed_font_dir.mkdir(parents=True, exist_ok=True)
        self._font_debug_dir: Optional[Path] = None

    def parse_book_info(self, html: str) -> Dict[str, Any]:
        """
        Parse a book info page and extract metadata and chapter structure.

        :param html: Raw HTML of the book info page.
        :return: Parsed metadata and chapter structure as a dictionary.
        """
        return parse_book_info(html)

    def parse_chapter(self, html_str: str, chapter_id: str) -> Dict[str, Any]:
        """
        :param html: Raw HTML of the chapter page.
        :param chapter_id: Identifier of the chapter being parsed.
        :return: Cleaned chapter content as plain text.
        """
        return parse_chapter(self, html_str, chapter_id)

    def is_encrypted(self, html_str: str) -> bool:
        """
        Return True if content is encrypted.

        :param html: Raw HTML of the chapter page.
        """
        return is_encrypted(html_str)

    def _init_cache_folders(self) -> None:
        """
        Prepare cache folders for plain/encrypted HTML and font debug data.
        Folders are only created if corresponding debug/save flags are enabled.
        """
        base = self._base_cache_dir

        # Font debug folder
        if self._save_font_debug and self.book_id:
            self._font_debug_dir = base / self.book_id / "font_debug"
            self._font_debug_dir.mkdir(parents=True, exist_ok=True)
        else:
            self._font_debug_dir = None

    def _on_book_id_set(self) -> None:
        self._init_cache_folders()
