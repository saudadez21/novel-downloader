#!/usr/bin/env python3
"""
novel_downloader.core.downloaders
---------------------------------

This subpackage contains concrete downloader implementations for
specific novel platforms.

Each downloader is responsible for orchestrating the full lifecycle
of retrieving, parsing, and saving novel content for a given source.
"""

__all__ = [
    "get_downloader",
    "CommonDownloader",
    "PiaotiaDownloader",
    "QianbiDownloader",
    "QidianDownloader",
]

from .common import CommonDownloader
from .piaotia import PiaotiaDownloader
from .qianbi import QianbiDownloader
from .qidian import QidianDownloader
from .registry import get_downloader
