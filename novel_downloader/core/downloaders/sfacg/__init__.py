#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.sfacg
---------------------------------------

"""

from .sfacg_async import SfacgAsyncDownloader
from .sfacg_sync import SfacgDownloader

__all__ = [
    "SfacgAsyncDownloader",
    "SfacgDownloader",
]
