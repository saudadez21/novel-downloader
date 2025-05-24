#!/usr/bin/env python3
"""
novel_downloader.core.downloaders
---------------------------------

This subpackage contains concrete downloader implementations for
specific novel platforms.

Each downloader is responsible for orchestrating the full lifecycle
of retrieving, parsing, and saving novel content for a given source.

Currently supported platforms:
- biquge (笔趣阁)
- qianbi (铅笔小说)
- qidian (起点中文网)
- common (通用架构)
"""

from .biquge import BiqugeAsyncDownloader, BiqugeDownloader
from .common import CommonAsyncDownloader, CommonDownloader
from .qianbi import QianbiAsyncDownloader, QianbiDownloader
from .qidian import QidianDownloader

__all__ = [
    "BiqugeAsyncDownloader",
    "BiqugeDownloader",
    "CommonAsyncDownloader",
    "CommonDownloader",
    "QianbiAsyncDownloader",
    "QianbiDownloader",
    "QidianDownloader",
]
