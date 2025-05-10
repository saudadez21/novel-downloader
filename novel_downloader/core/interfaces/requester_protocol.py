#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.interfaces.requester_protocol
--------------------------------------------------

Defines the RequesterProtocol interface for fetching raw HTML or JSON
for book info pages, individual chapters, managing request lifecycle,
and optionally retrieving a user's authenticated bookcase.
"""

from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class RequesterProtocol(Protocol):
    """
    A requester must be able to fetch raw HTML/data for:
      - a book's info page,
      - a specific chapter page.
    """

    def login(self, max_retries: int = 3, manual_login: bool = False) -> bool:
        """
        Attempt to log in
        """
        ...

    def get_book_info(self, book_id: str, wait_time: Optional[int] = None) -> str:
        """
        Fetch the raw HTML (or JSON) of the book info page.

        :param book_id: The book identifier.
        :param wait_time: Base number of seconds to wait before returning content.
        :return: The page content as a string.
        """
        ...

    def get_book_chapter(
        self, book_id: str, chapter_id: str, wait_time: Optional[int] = None
    ) -> str:
        """
        Fetch the raw HTML (or JSON) of a single chapter.

        :param book_id: The book identifier.
        :param chapter_id: The chapter identifier.
        :param wait_time: Base number of seconds to wait before returning content.
        :return: The chapter content as a string.
        """
        ...

    def shutdown(self) -> None:
        """
        Shutdown and cleans up resources.
        """
        ...

    def get_bookcase(self, wait_time: Optional[int] = None) -> str:
        """
        Optional: Retrieve the HTML content of the authenticated user's bookcase page.

        :param wait_time: Base number of seconds to wait before returning content.
        :return: The HTML markup of the bookcase page.
        """
        ...
