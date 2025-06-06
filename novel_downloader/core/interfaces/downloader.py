#!/usr/bin/env python3
"""
novel_downloader.core.interfaces.downloader
-------------------------------------------

This module defines the DownloaderProtocol, a structural interface
that outlines the expected behavior of any downloader class.
"""

from collections.abc import Awaitable, Callable
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class DownloaderProtocol(Protocol):
    """
    Protocol for fully-asynchronous downloader classes.

    Defines the expected interface for any downloader implementation,
    including both batch and single book downloads,
    as well as optional pre-download hooks.
    """

    async def download(
        self,
        book_id: str,
        *,
        progress_hook: Callable[[int, int], Awaitable[None]] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Download logic for a single book.

        :param book_id: The identifier of the book.
        :param progress_hook: (optional) Called after each chapter;
                                args: completed_count, total_count.
        """
        ...

    async def download_many(
        self,
        book_ids: list[str],
        *,
        progress_hook: Callable[[int, int], Awaitable[None]] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Batch download entry point.

        :param book_ids: List of book IDs to download.
        :param progress_hook: (optional) Called after each chapter;
                                args: completed_count, total_count.
        """
        ...
