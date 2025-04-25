#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.interfaces.downloader_protocol
----------------------------------------------------

This module defines the DownloaderProtocol, a structural interface
that outlines the expected behavior of any downloader class.
"""

from typing import List, Protocol


class DownloaderProtocol(Protocol):
    """
    Protocol for downloader classes.

    Defines the expected interface for any downloader implementation,
    including both batch and single book downloads,
    as well as optional pre-download hooks.
    """

    def download(self, book_ids: List[str]) -> None:
        """
        Batch download entry point.

        :param book_ids: List of book IDs to download.
        """
        ...

    def download_one(self, book_id: str) -> None:
        """
        Download logic for a single book.

        :param book_id: The identifier of the book.
        """
        ...
