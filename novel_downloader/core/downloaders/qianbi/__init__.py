#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.qianbi
----------------------------------------

"""

from .qianbi_async import QianbiAsyncDownloader
from .qianbi_sync import QianbiDownloader

__all__ = [
    "QianbiAsyncDownloader",
    "QianbiDownloader",
]
