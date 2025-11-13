#!/usr/bin/env python3
"""
novel_downloader.plugins.protocols.processor
--------------------------------------------

Protocol defining the interface for text processors that operate
on book and chapter data before export or further use.
"""

from typing import Any, Protocol

from novel_downloader.schemas import BookInfoDict, ChapterDict


class ProcessorProtocol(Protocol):
    """
    Protocol for a processor that modifies or enriches parsed data.

    A processor performs transformations on book metadata or chapter content,
    typically for cleanup, formatting, or metadata augmentation.
    """

    def __init__(self, config: dict[str, Any]) -> None:
        """
        Initialize the processor with a configuration dictionary.

        :param config: Processor-specific settings.
        """
        ...

    def process_book_info(self, book_info: BookInfoDict) -> BookInfoDict:
        """
        Process and transform book-level metadata.

        :param book_info: Parsed :class:`BookInfoDict`.
        :return: Modified or original book metadata.
        """
        ...

    def process_chapter(self, chapter: ChapterDict) -> ChapterDict:
        """
        Process and transform a single chapter.

        :param chapter: Parsed :class:`ChapterDict`.
        :return: Modified or original chapter data.
        """
        ...
