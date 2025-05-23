#!/usr/bin/env python3
"""
novel_downloader.core.downloaders
---------------------------------

This subpackage contains concrete downloader implementations for
specific novel platforms.

Each downloader is responsible for orchestrating the full lifecycle
of retrieving, parsing, and saving novel content for a given source.
"""

from .biquge import BiqugeAsyncDownloader, BiqugeDownloader
from .common import CommonAsyncDownloader, CommonDownloader
from .qidian import QidianDownloader

__all__ = [
    "BiqugeAsyncDownloader",
    "BiqugeDownloader",
    "CommonAsyncDownloader",
    "CommonDownloader",
    "QidianDownloader",
]
