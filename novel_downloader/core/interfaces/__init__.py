#!/usr/bin/env python3
"""
novel_downloader.core.interfaces
--------------------------------

This package centralizes the protocol definitions used across the
system to promote interface-based design and type-safe dependency
injection.

Included protocols:
- DownloaderProtocol
- ParserProtocol
- RequesterProtocol
- SaverProtocol
"""

from .async_downloader import AsyncDownloaderProtocol
from .async_requester import AsyncRequesterProtocol
from .parser import ParserProtocol
from .saver import SaverProtocol
from .sync_downloader import SyncDownloaderProtocol
from .sync_requester import SyncRequesterProtocol

__all__ = [
    "AsyncDownloaderProtocol",
    "AsyncRequesterProtocol",
    "ParserProtocol",
    "SaverProtocol",
    "SyncDownloaderProtocol",
    "SyncRequesterProtocol",
]
