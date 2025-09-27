#!/usr/bin/env python3
"""
novel_downloader.plugins.base.parser
------------------------------------

Abstract base class providing common behavior for site-specific parsers.
"""

import abc
import re
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from novel_downloader.schemas import BookInfoDict, ChapterDict, ParserConfig


class BaseParser(abc.ABC):
    """
    BaseParser defines the interface for extracting book metadata and chapter content
    from raw HTML.

    Subclasses must implement actual parsing logic for specific sites.
    """

    site_name: str
    ADS: set[str] = set()

    _SPACE_RE = re.compile(r"\s+")

    def __init__(self, config: ParserConfig):
        """
        Initialize the parser with a configuration object.

        :param config: ParserConfig object controlling parsing behavior.
        """
        self._book_id: str | None = None

        self._fontocr_cfg = config.fontocr_cfg
        self._save_font_debug = config.save_font_debug
        self._decode_font: bool = config.decode_font
        self._batch_size = config.batch_size
        self._use_truncation = config.use_truncation
        self._base_cache_dir = Path(config.cache_dir)

        self._ad_pattern = self._compile_ads_pattern()

    @abc.abstractmethod
    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        """
        Parse and return a dictionary of book information from the raw HTML.

        :param html_list: The HTML list of a book's info pages.
        :return: A dict containing metadata like title, author, chapters list, etc.
        """
        ...

    @abc.abstractmethod
    def parse_chapter(
        self,
        html_list: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        """
        Parse chapter page and extract the content of one chapter.

        :param html_list: The HTML list of the chapter pages.
        :param chapter_id: Identifier of the chapter being parsed.
        :return: The chapter's data.
        """
        ...

    def _compile_ads_pattern(self) -> re.Pattern[str] | None:
        """
        Compile a regex pattern from the ADS list, or return None if no ADS.
        """
        if not self.ADS:
            return None

        return re.compile("|".join(self.ADS))

    def _is_ad_line(self, line: str) -> bool:
        """
        Check if a line contains any ad text.

        :param line: Single text line.
        :return: True if line matches ad pattern, else False.
        """
        return bool(self._ad_pattern and self._ad_pattern.search(line))

    def _filter_ads(self, lines: Iterable[str]) -> list[str]:
        """
        Filter out lines containing any ad text defined in ADS.

        :param lines: Iterable of text lines (e.g. chapter content).
        :return: List of lines with ads removed.
        """
        if not self._ad_pattern:
            return list(lines)
        return [line for line in lines if not self._ad_pattern.search(line)]

    @classmethod
    def _norm_space(cls, s: str, c: str = " ") -> str:
        """
        collapse any run of whitespace (incl. newlines, full-width spaces)

        :param s: Input string to normalize.
        :param c: Replacement character to use for collapsed whitespace.
        """
        return cls._SPACE_RE.sub(c, s).strip()

    @staticmethod
    def _first_str(xs: list[str], replaces: list[tuple[str, str]] | None = None) -> str:
        replaces = replaces or []
        value: str = xs[0].strip() if xs else ""
        for old, new in replaces:
            value = value.replace(old, new)
        return value.strip()

    @staticmethod
    def _join_strs(xs: list[str], replaces: list[tuple[str, str]] | None = None) -> str:
        replaces = replaces or []
        value = "\n".join(s.strip() for s in xs if s and s.strip())
        for old, new in replaces:
            value = value.replace(old, new)
        return value.strip()
