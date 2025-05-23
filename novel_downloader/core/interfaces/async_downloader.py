#!/usr/bin/env python3
"""
novel_downloader.core.interfaces.async_downloader
----------------------------------------------------------

This module defines the AsyncDownloaderProtocol, a structural interface
that outlines the expected behavior of any downloader class.
"""

from typing import Protocol


class AsyncDownloaderProtocol(Protocol):
    """
    Protocol for fully-asynchronous downloader classes.

    Defines the expected interface for any downloader implementation,
    including both batch and single book downloads,
    as well as optional pre-download hooks.
    """

    async def download(self, book_ids: list[str]) -> None:
        """
        Batch download entry point.

        :param book_ids: List of book IDs to download.
        """
        ...

    async def download_one(self, book_id: str) -> None:
        """
        Download logic for a single book.

        :param book_id: The identifier of the book.
        """
        ...
