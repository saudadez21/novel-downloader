#!/usr/bin/env python3
"""
novel_downloader.plugins.protocols.fetcher
------------------------------------------

Protocol defining the interface for asynchronous fetching, login, and session management
"""

import types
from pathlib import Path
from typing import Any, Literal, Protocol, Self

from novel_downloader.schemas import LoginField


class FetcherProtocol(Protocol):
    """
    An async requester must be able to fetch raw HTML/data for:
      * a book's info page,
      * a specific chapter page,
    and manage login/shutdown asynchronously.
    """

    async def init(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Perform async initialization, such as creating a session.

        This should be called before using any other method
        if initialization is required.
        """
        ...

    async def close(self) -> None:
        """
        Shutdown and clean up any resources.
        """
        ...

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
        :return: The page content as string list.
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
        :return: The page content as string list.
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

    async def download_images(
        self,
        img_dir: Path,
        urls: list[str],
        batch_size: int = 10,
        *,
        on_exist: Literal["overwrite", "skip", "rename"] = "skip",
    ) -> None:
        """
        Download images to `img_dir` in batches.

        :param img_dir: Destination folder.
        :param urls: List of image URLs (http/https).
        :param batch_size: Concurrency per batch.
        :param on_exist: What to do when file exists.
        """
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

    async def __aenter__(self) -> Self:
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        tb: types.TracebackType | None,
    ) -> None:
        ...
