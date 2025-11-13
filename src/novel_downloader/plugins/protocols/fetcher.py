#!/usr/bin/env python3
"""
novel_downloader.plugins.protocols.fetcher
------------------------------------------

Protocol defining the interface for asynchronous fetching, authentication,
and session management for site-specific clients.

This protocol abstracts the behavior of network requesters that
retrieve book metadata, chapters, and media files from supported
novel platforms.
"""

import types
from pathlib import Path
from typing import Any, Literal, Protocol, Self

from novel_downloader.schemas import LoginField, MediaResource


class FetcherProtocol(Protocol):
    """
    Protocol for an asynchronous network fetcher.

    Implementations are responsible for performing HTTP requests,
    handling login sessions, caching state, and downloading
    both textual and binary resources.
    """

    async def init(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Perform asynchronous initialization.

        Typical responsibilities include creating a network session,
        applying proxy settings, or restoring state.

        This should be called before invoking any other fetch operation.
        """
        ...

    async def close(self) -> None:
        """
        Gracefully close and clean up all network or file resources.

        Should terminate open sessions and release internal caches.
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
        Attempt to authenticate asynchronously.

        Implementations should support login via credentials,
        cookies, or a combination of both.

        :param username: Username or account identifier.
        :param password: Account password.
        :param cookies: Optional cookie mapping for session restoration.
        :param attempt: Retry counter for recursive or multi-step login.
        :returns: ``True`` if login succeeded, otherwise ``False``.
        """
        ...

    @property
    def is_logged_in(self) -> bool:
        """
        Whether the fetcher is currently authenticated.

        :return: ``True`` if an active session is authenticated.
        """
        ...

    @property
    def login_fields(self) -> list[LoginField]:
        """
        List of fields required for interactive or programmatic login.

        :return: A list of :class:`LoginField` describing credential fields
                 (e.g. username, password, captcha, etc.).
        """
        ...

    async def fetch_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Retrieve the raw HTML or JSON content of a book's info page.

        :param book_id: The book identifier on the target site.
        :return: A list of strings containing the raw page data.
        """
        ...

    async def fetch_chapter_content(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Retrieve the raw HTML or JSON content of a single chapter.

        :param chapter_id: The chapter identifier.
        :param book_id: Optional book identifier if available.
        :return: A list of strings containing the raw page data.
        """
        ...

    async def fetch_data(self, url: str, **kwargs: Any) -> bytes:
        """
        Fetch arbitrary binary data from a remote URL.

        Useful for retrieving cover images, font files, or
        other non-HTML assets directly.

        :param url: The target URL.
        :return: The raw response body as bytes.
        """
        ...

    async def fetch_image(
        self,
        url: str,
        img_dir: Path,
        *,
        name: str | None = None,
        on_exist: Literal["overwrite", "skip"] = "skip",
    ) -> Path | None:
        """
        Download a single image and return its saved path.

        :param url: Image URL.
        :param img_dir: Destination folder.
        :param name: Optional explicit filename (without suffix).
        :param on_exist: What to do when file exists.
        :return: Path of saved image, or None if failed/skipped.
        """
        ...

    async def fetch_images(
        self,
        img_dir: Path,
        urls: list[str],
        *,
        on_exist: Literal["overwrite", "skip"] = "skip",
        concurrent: int = 5,
    ) -> None:
        """
        Download image URLs directly to disk.

        :param img_dir: Destination directory.
        :param urls: List of image URLs.
        :param on_exist: Behavior when file already exists.
        :param concurrent: Maximum number of concurrent downloads.
        """
        ...

    async def fetch_media(
        self,
        resource: MediaResource,
        media_dir: Path,
        *,
        on_exist: Literal["overwrite", "skip"] = "skip",
    ) -> Path | None:
        """
        Download or persist a single media resource entry.

        :param resource: A :class:`MediaResource` entry.
        :param media_dir: Target directory to store the media.
        :param on_exist: Behavior when file already exists.
        :return: Saved path or ``None`` if skipped.
        """
        ...

    async def fetch_medias(
        self,
        media_dir: Path,
        resources: list[MediaResource],
        batch_size: int = 10,
        *,
        on_exist: Literal["overwrite", "skip"] = "skip",
    ) -> None:
        """
        Process and persist a list of media resources asynchronously.

        :param media_dir: Destination directory.
        :param resources: List of :class:`MediaResource` items.
        :param batch_size: Number of concurrent tasks per batch.
        :param on_exist: Behavior when existing files are found.
        """
        ...

    async def load_state(self) -> bool:
        """
        Restore session state from persistent storage.

        This allows the fetcher to resume a previous authenticated session
        without requiring manual login.

        :return: ``True`` if the session state was successfully restored.
        """
        ...

    async def save_state(self) -> bool:
        """
        Persist the current session state to a file or other storage backend.

        The saved state should allow later recovery of authentication cookies
        or tokens.

        :return: ``True`` if the session state was successfully saved.
        """
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
