#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.parsers.base_parser
-----------------------------------------

This module defines the BaseParser abstract class, which implements the
ParserProtocol interface and provides a structured foundation for
site-specific parsers.

BaseParser manages internal parser state and enforces
a standard parsing interface for:
- Book info pages (e.g. metadata, chapter list)
- Chapter pages (e.g. textual content)
"""

import abc
from pathlib import Path
from typing import Any, Dict, Optional

from novel_downloader.config import ParserConfig
from novel_downloader.core.interfaces import ParserProtocol


class BaseParser(ParserProtocol, abc.ABC):
    """
    BaseParser defines the interface for extracting book metadata and chapter content
    from raw HTML.

    This base class manages internal book state (e.g. current book ID) and supports
    configuration-driven behavior such as content cleaning or formatting.

    Subclasses must implement actual parsing logic for specific sites.
    """

    def __init__(self, config: ParserConfig):
        """
        Initialize the parser with a configuration object.

        :param config: ParserConfig object controlling parsing behavior.
        """
        self._config = config
        self._book_id: Optional[str] = None

        self._base_cache_dir = Path(config.cache_dir)

    @abc.abstractmethod
    def parse_book_info(self, html: str) -> Dict[str, Any]:
        """
        Parse a book info page and extract metadata and chapter structure.

        Depending on the site structure, the return dict may include a
        flat `chapters` list or nested `volumes` with chapter groups.

        :param html: Raw HTML of the book info page.
        :return: Parsed metadata and chapter structure as a dictionary.
        """
        ...

    @abc.abstractmethod
    def parse_chapter(self, html_str: str, chapter_id: str) -> Dict[str, Any]:
        """
        Parse a single chapter page and extract clean text or simplified HTML.

        :param html: Raw HTML of the chapter page.
        :param chapter_id: Identifier of the chapter being parsed.
        :return: Cleaned chapter content as plain text or minimal HTML.
        """
        ...

    @property
    def book_id(self) -> Optional[str]:
        """
        Current book ID in context.

        :return: The current book identifier.
        """
        return self._book_id

    @book_id.setter
    def book_id(self, value: str) -> None:
        """
        Set current book ID and update debug paths if needed.

        :param value: Book identifier.
        """
        self._book_id = value
        self._on_book_id_set()

    def _on_book_id_set(self) -> None:
        """
        Hook called when a new book ID is set.
        Subclasses can override this to initialize
        book-related folders or states.
        """
        pass
