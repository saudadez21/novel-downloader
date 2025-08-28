#!/usr/bin/env python3
"""
novel_downloader.core.downloaders
---------------------------------

Downloader implementations for retrieving novels from different sources
"""

__all__ = [
    "get_downloader",
    "CommonDownloader",
    "QianbiDownloader",
    "QidianDownloader",
]

from .common import CommonDownloader
from .qianbi import QianbiDownloader
from .qidian import QidianDownloader
from .registry import get_downloader
