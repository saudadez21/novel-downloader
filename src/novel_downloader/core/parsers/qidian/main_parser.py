#!/usr/bin/env python3
"""
novel_downloader.core.parsers.qidian.main_parser
------------------------------------------------

Main parser class for handling Qidian HTML
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from novel_downloader.core.parsers.base import BaseParser
from novel_downloader.core.parsers.registry import register_parser
from novel_downloader.models import (
    BookInfoDict,
    ChapterDict,
    ParserConfig,
)
from novel_downloader.utils.constants import DATA_DIR
from novel_downloader.utils.cookies import get_cookie_value

from .book_info_parser import parse_book_info
from .chapter_router import parse_chapter
from .utils import is_encrypted

logger = logging.getLogger(__name__)


@register_parser(
    site_keys=["qidian", "qd"],
)
class QidianParser(BaseParser):
    """
    Parser for 起点中文网 site.
    """

    def __init__(
        self,
        config: ParserConfig,
        fuid: str = "",
    ):
        """
        Initialize the QidianParser with the given configuration.

        :param config: ParserConfig object controlling:
        """
        super().__init__(config)

        self._fixed_font_dir: Path = self._base_cache_dir / "fixed_fonts"
        self._fixed_font_dir.mkdir(parents=True, exist_ok=True)
        self._debug_dir: Path = Path.cwd() / "debug"

        state_files = [
            DATA_DIR / "qidian" / "session_state.cookies",
        ]
        self._fuid: str = fuid or get_cookie_value(state_files, "ywguid")

    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        """
        Parse a book info page and extract metadata and chapter structure.

        :param html_list: Raw HTML of the book info page.
        :return: Parsed metadata and chapter structure as a dictionary.
        """
        if not html_list:
            return None
        return parse_book_info(html_list[0])

    def parse_chapter(
        self,
        html_list: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        """
        :param html_list: Raw HTML of the chapter page.
        :param chapter_id: Identifier of the chapter being parsed.
        :return: Cleaned chapter content as plain text.
        """
        if not html_list:
            return None
        return parse_chapter(self, html_list[0], chapter_id)

    def is_encrypted(self, html_str: str) -> bool:
        """
        Return True if content is encrypted.

        :param html: Raw HTML of the chapter page.
        """
        return is_encrypted(html_str)

    @property
    def save_font_debug(self) -> bool:
        return self._config.save_font_debug
