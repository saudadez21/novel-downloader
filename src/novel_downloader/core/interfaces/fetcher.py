#!/usr/bin/env python3
"""
novel_downloader.core.interfaces.fetcher
----------------------------------------

Defines the Async FetcherProtocol interface for fetching raw HTML or JSON
for book info pages, individual chapters, managing request lifecycle
"""

import types
from typing import Any, Protocol, Self, runtime_checkable

from novel_downloader.models import LoginField


@runtime_checkable
class FetcherProtocol(Protocol):
    """
    An async requester must be able to fetch raw HTML/data for:
      - a book's info page,
      - a specific chapter page,
    and manage login/shutdown asynchronously.
    """

    async def login(
        self,
        username: str = "",
        password: str = "",
        cookies: dict[str, str] | None = None,
        attempt: int = 1,
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
        :return: The chapter content as string.
        """
        ...

    async def get_bookcase(
        self,
        **kwargs: Any,
    ) -> list[str]:
        """
        Optional: Retrieve the HTML content of the authenticated
        user's bookcase page asynchronously.

        :return: The HTML markup of the bookcase page.
        """
        ...

    async def fetch(
        self,
        url: str,
        **kwargs: Any,
    ) -> str:
        """
        Perform a generic HTTP request and return the response body as text.

        :param url: The URL to request.
        :return: The response content as a string (HTML or JSON or plain text).
        """
        ...

    async def init(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Perform async initialization, such as
        launching a browser or creating a session.

        This should be called before using any other method
        if initialization is required.
        """
        ...

    async def close(self) -> None:
        """
        Shutdown and clean up any resources.
        """
        ...

    async def load_state(self) -> bool:
        """
        Restore session state from a persistent storage,
        allowing the requester to resume a previous authenticated session.

        :return: True if the session state was successfully loaded and applied.
        """
        ...

    async def save_state(self) -> bool:
        """
        Persist the current session state to a file
        or other storage, so that it can be restored in future sessions.

        :return: True if the session state was successfully saved.
        """
        ...

    async def set_interactive_mode(self, enable: bool) -> bool:
        """
        Enable or disable interactive mode for manual login.

        :param enable: True to enable, False to disable interactive mode.
        :return: True if operation or login check succeeded, False otherwise.
        """
        ...

    @property
    def requester_type(self) -> str:
        ...

    @property
    def is_logged_in(self) -> bool:
        """
        Indicates whether the requester is currently authenticated.
        """
        ...

    @property
    def login_fields(self) -> list[LoginField]:
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        tb: types.TracebackType | None,
    ) -> None:
        ...

    async def __aenter__(self) -> Self:
        ...
