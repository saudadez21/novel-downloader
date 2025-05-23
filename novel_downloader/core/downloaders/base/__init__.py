#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.base
--------------------------------------

"""

from .base_async import BaseAsyncDownloader
from .base_sync import BaseDownloader

__all__ = [
    "BaseAsyncDownloader",
    "BaseDownloader",
]
