#!/usr/bin/env python3
"""
novel_downloader.core.interfaces.downloader
-------------------------------------------

This module defines the DownloaderProtocol, a structural interface
that outlines the expected behavior of any downloader class.
"""

from collections.abc import Awaitable, Callable
from typing import Any, Protocol, runtime_checkable

from novel_downloader.models import BookConfig


@runtime_checkable
class DownloaderProtocol(Protocol):
    """
    Protocol for async downloader implementations.

    Uses BookConfig (with book_id, optional start_id/end_id/ignore_ids)
    for both single and batch downloads.
    """

    async def download(
        self,
        book: BookConfig,
        *,
        progress_hook: Callable[[int, int], Awaitable[None]] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Download a single book.

        :param book: BookConfig with at least 'book_id'.
        :param progress_hook: Optional async callback after each chapter.
                                args: completed_count, total_count.
        """
        ...

    async def download_many(
        self,
        books: list[BookConfig],
        *,
        progress_hook: Callable[[int, int], Awaitable[None]] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Download multiple books.

        :param books: List of BookConfig entries.
        :param progress_hook: Optional async callback after each chapter.
                                args: completed_count, total_count.
        """
        ...
