#!/usr/bin/env python3
"""
novel_downloader.core.interfaces.sync_requester
-----------------------------------------------

Defines the RequesterProtocol interface for fetching raw HTML or JSON
for book info pages, individual chapters, managing request lifecycle,
and optionally retrieving a user's authenticated bookcase.
"""

from typing import Any, Literal, Protocol, runtime_checkable


@runtime_checkable
class SyncRequesterProtocol(Protocol):
    """
    A requester must be able to fetch raw HTML/data for:
      - a book's info page,
      - a specific chapter page.
    """

    def is_async(self) -> Literal[False]:
        ...

    def login(
        self,
        username: str = "",
        password: str = "",
        manual_login: bool = False,
        **kwargs: Any,
    ) -> bool:
        """
        Attempt to log in
        """
        ...

    def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML (or JSON) of the book info page.

        :param book_id: The book identifier.
        :return: The page content as a string.
        """
        ...

    def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML (or JSON) of a single chapter.

        :param book_id: The book identifier.
        :param chapter_id: The chapter identifier.
        :return: The chapter content as a string.
        """
        ...

    def get_bookcase(
        self,
        page: int = 1,
        **kwargs: Any,
    ) -> list[str]:
        """
        Optional: Retrieve the HTML content of the authenticated user's bookcase page.

        :param page: Page idx
        :return: The HTML markup of the bookcase page.
        """
        ...

    def close(self) -> None:
        """
        Shutdown and cleans up resources.
        """
        ...
