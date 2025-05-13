#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.interfaces.async_requester_protocol
--------------------------------------------------------

Defines the AsyncRequesterProtocol interface for fetching raw HTML or JSON
for book info pages, individual chapters, managing request lifecycle,
and optionally retrieving a user's authenticated bookcase — all in async style.
"""

from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class AsyncRequesterProtocol(Protocol):
    """
    An async requester must be able to fetch raw HTML/data for:
      - a book's info page,
      - a specific chapter page,
    and manage login/shutdown asynchronously.
    """

    async def login(self, max_retries: int = 3, manual_login: bool = False) -> bool:
        """
        Attempt to log in asynchronously.
        :returns: True if login succeeded.
        """
        ...

    async def get_book_info(self, book_id: str, wait_time: Optional[int] = None) -> str:
        """
        Fetch the raw HTML (or JSON) of the book info page asynchronously.

        :param book_id: The book identifier.
        :param wait_time: Base number of seconds to wait before returning content.
        :return: The page content as a string.
        """
        ...

    async def get_book_chapter(
        self, book_id: str, chapter_id: str, wait_time: Optional[int] = None
    ) -> str:
        """
        Fetch the raw HTML (or JSON) of a single chapter asynchronously.

        :param book_id: The book identifier.
        :param chapter_id: The chapter identifier.
        :param wait_time: Base number of seconds to wait before returning content.
        :return: The chapter content as a string.
        """
        ...

    async def get_bookcase(self, wait_time: Optional[int] = None) -> str:
        """
        Optional: Retrieve the HTML content of the authenticated
        user's bookcase page asynchronously.

        :param wait_time: Base number of seconds to wait before returning content.
        :return: The HTML markup of the bookcase page.
        """
        ...

    async def shutdown(self) -> None:
        """
        Shutdown and clean up any resources (e.g., close aiohttp session).
        """
        ...
