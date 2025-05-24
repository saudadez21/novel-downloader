#!/usr/bin/env python3
"""
novel_downloader.core.interfaces.async_requester
--------------------------------------------------------

Defines the AsyncRequesterProtocol interface for fetching raw HTML or JSON
for book info pages, individual chapters, managing request lifecycle,
and optionally retrieving a user's authenticated bookcase.
"""

from typing import Any, Literal, Protocol, runtime_checkable


@runtime_checkable
class AsyncRequesterProtocol(Protocol):
    """
    An async requester must be able to fetch raw HTML/data for:
      - a book's info page,
      - a specific chapter page,
    and manage login/shutdown asynchronously.
    """

    def is_async(self) -> Literal[True]:
        ...

    async def login(
        self,
        username: str = "",
        password: str = "",
        manual_login: bool = False,
        **kwargs: Any,
    ) -> bool:
        """
        Attempt to log in asynchronously.
        :returns: True if login succeeded.
        """
        ...

    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML (or JSON) of the book info page asynchronously.

        :param book_id: The book identifier.
        :return: The page content as a string.
        """
        ...

    async def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML (or JSON) of a single chapter asynchronously.

        :param book_id: The book identifier.
        :param chapter_id: The chapter identifier.
        :return: The chapter content as a string.
        """
        ...

    async def get_bookcase(
        self,
        page: int = 1,
        **kwargs: Any,
    ) -> list[str]:
        """
        Optional: Retrieve the HTML content of the authenticated
        user's bookcase page asynchronously.

        :return: The HTML markup of the bookcase page.
        """
        ...

    async def close(self) -> None:
        """
        Shutdown and clean up any resources (e.g., close aiohttp session).
        """
        ...
