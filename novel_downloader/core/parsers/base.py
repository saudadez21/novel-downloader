#!/usr/bin/env python3
"""
novel_downloader.core.parsers.base
----------------------------------

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
from typing import Any

from novel_downloader.core.interfaces import ParserProtocol
from novel_downloader.models import ChapterDict, ParserConfig


class BaseParser(ParserProtocol, abc.ABC):
    """
    BaseParser defines the interface for extracting book metadata and chapter content
    from raw HTML.

    This base class manages internal book state (e.g. current book ID) and supports
    configuration-driven behavior such as content cleaning or formatting.

    Subclasses must implement actual parsing logic for specific sites.
    """

    def __init__(
        self,
        config: ParserConfig,
    ):
        """
        Initialize the parser with a configuration object.

        :param config: ParserConfig object controlling parsing behavior.
        """
        self._config = config
        self._book_id: str | None = None

        self._base_cache_dir = Path(config.cache_dir)
        self._cache_dir = self._base_cache_dir

    @abc.abstractmethod
    def parse_book_info(
        self,
        html_list: list[str],
        **kwargs: Any,
    ) -> dict[str, Any]:
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
        Parse and return the text content of one chapter.

        :param html_list: The HTML list of the chapter pages.
        :param chapter_id: Identifier of the chapter being parsed.
        :return: The chapter's text.
        """
        ...

    @property
    def book_id(self) -> str | None:
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
        self._cache_dir = self._base_cache_dir / value
        self._on_book_id_set()

    def _on_book_id_set(self) -> None:
        """
        Hook called when a new book ID is set.
        Subclasses can override this to initialize
        book-related folders or states.
        """
        pass
