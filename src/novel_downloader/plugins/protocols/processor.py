#!/usr/bin/env python3
"""
novel_downloader.plugins.protocols.processor
--------------------------------------------

This protocol defines a common interface for text processors
that operate on book metadata and chapter content.
"""

from typing import Any, Protocol

from novel_downloader.schemas import BookInfoDict, ChapterDict


class ProcessorProtocol(Protocol):
    """
    A processor defines operations to transform book and chapter data
    before export or further use.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        ...

    def process_book_info(self, book_info: BookInfoDict) -> BookInfoDict:
        """
        Process and transform book-level metadata.

        :param book_info: The book's metadata dictionary as parsed.
        :return: The modified (or unmodified) metadata dictionary.
        """
        ...

    def process_chapter(self, chapter: ChapterDict) -> ChapterDict:
        """
        Process and transform a single chapter's data.

        :param chapter: A dictionary containing chapter metadata and content.
        :return: The modified (or unmodified) chapter dictionary.
        """
        ...
