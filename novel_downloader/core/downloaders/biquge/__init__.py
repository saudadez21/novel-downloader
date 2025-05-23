#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.biquge
----------------------------------------

"""

from .biquge_async import BiqugeAsyncDownloader
from .biquge_sync import BiqugeDownloader

__all__ = [
    "BiqugeAsyncDownloader",
    "BiqugeDownloader",
]
