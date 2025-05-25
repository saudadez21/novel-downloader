#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.yamibo
----------------------------------------

"""

from .yamibo_async import YamiboAsyncDownloader
from .yamibo_sync import YamiboDownloader

__all__ = [
    "YamiboAsyncDownloader",
    "YamiboDownloader",
]
