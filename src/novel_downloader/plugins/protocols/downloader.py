#!/usr/bin/env python3
"""
novel_downloader.plugins.protocols.downloader
---------------------------------------------

Protocol defining the interface for asynchronous book downloaders.
"""

import asyncio
from collections.abc import Awaitable, Callable
from typing import Any, Protocol

from novel_downloader.schemas import BookConfig


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
        cancel_event: asyncio.Event | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Download a single book.

        :param book: BookConfig with at least 'book_id'.
        :param progress_hook: Optional async callback after each chapter.
                                args: completed_count, total_count.
        :param cancel_event: Optional asyncio.Event to allow cancellation.
        """
        ...

    async def download_many(
        self,
        books: list[BookConfig],
        *,
        progress_hook: Callable[[int, int], Awaitable[None]] | None = None,
        cancel_event: asyncio.Event | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Download multiple books.

        :param books: List of BookConfig entries.
        :param progress_hook: Optional async callback after each chapter.
                                args: completed_count, total_count.
        :param cancel_event: Optional asyncio.Event to allow cancellation.
        """
        ...
