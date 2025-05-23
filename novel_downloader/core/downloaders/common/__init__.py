#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.common
----------------------------------------

"""

from .common_async import CommonAsyncDownloader
from .common_sync import CommonDownloader

__all__ = [
    "CommonAsyncDownloader",
    "CommonDownloader",
]
