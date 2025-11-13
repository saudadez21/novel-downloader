#!/usr/bin/env python3
"""
novel_downloader.plugins.protocols.parser
-----------------------------------------

Protocol defining the interface for parsing book metadata and chapter content.

A parser is responsible for extracting structured data from the raw
HTML or JSON returned by a :class:`FetcherProtocol`.
"""

from typing import Any, Protocol

from novel_downloader.schemas import BookInfoDict, ChapterDict


class ParserProtocol(Protocol):
    """
    Protocol for a site-specific parser implementation.

    A parser transforms raw HTML or JSON data fetched from a site into
    structured Python dictionaries suitable for downstream processing.
    """

    def parse_book_info(
        self,
        raw_pages: list[str],
        **kwargs: Any,
    ) -> BookInfoDict | None:
        """
        Parse book-level metadata from raw HTML, JSON, or text responses.

        Usually called with the result of
        :meth:`FetcherProtocol.fetch_book_info`.

        :param raw_pages: Raw page contents for the book info section.
        :return: Parsed :class:`BookInfoDict`, or ``None`` if parsing fails.
        """
        ...

    def parse_chapter_content(
        self,
        raw_pages: list[str],
        chapter_id: str,
        **kwargs: Any,
    ) -> ChapterDict | None:
        """
        Parse a chapter's data from raw HTML, JSON, or text responses.

        Usually called with the result of
        :meth:`FetcherProtocol.fetch_chapter_content`.

        :param raw_pages: Raw page contents for the chapter.
        :param chapter_id: Identifier of the chapter being parsed.
        :return: Parsed :class:`ChapterDict`, or ``None`` if parsing fails.
        """
        ...
