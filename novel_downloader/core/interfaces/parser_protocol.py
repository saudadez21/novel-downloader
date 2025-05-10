#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.interfaces.parser_protocol
------------------------------------------------

Defines the ParserProtocol interface for extracting book metadata,
parsing individual chapter content, and setting parser context via book_id.
"""

from typing import Any, Dict, Protocol, runtime_checkable


@runtime_checkable
class ParserProtocol(Protocol):
    """
    A parser must be able to:
      - extract book metadata from an HTML string,
      - extract a single chapter's text from an HTML string,
      - accept a book_id context for multi-step workflows.
    """

    def parse_book_info(self, html_str: str) -> Dict[str, Any]:
        """
        Parse and return a dictionary of book information from the raw HTML.

        :param html_str: The HTML of a book's info page.
        :return: A dict containing metadata like title, author, chapters list, etc.
        """
        ...

    def parse_chapter(self, html_str: str, chapter_id: str) -> Dict[str, Any]:
        """
        Parse and return the text content of one chapter.

        :param html_str: The HTML of the chapter page.
        :param chapter_id: Identifier of the chapter being parsed.
        :return: The chapter's text.
        """
        ...
