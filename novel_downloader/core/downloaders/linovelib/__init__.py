#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.linovelib
-------------------------------------------

"""

from .linovelib_async import LinovelibAsyncDownloader
from .linovelib_sync import LinovelibDownloader

__all__ = [
    "LinovelibAsyncDownloader",
    "LinovelibDownloader",
]
