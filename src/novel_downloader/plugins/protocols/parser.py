#!/usr/bin/env python3
"""
novel_downloader.plugins.protocols.parser
-----------------------------------------

Protocol defining the interface for parsing book metadata and chapter content.
"""

from typing import Any, Protocol

from novel_downloader.schemas import BookInfoDict, ChapterDict


class ParserProtocol(Protocol):
    """
    A parser must be able to:
      * extract book metadata from an HTML string,
      * extract a single chapter's text from an HTML string
    """

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
