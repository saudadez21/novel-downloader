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
- esjzone (ESJ Zone)
- qianbi (铅笔小说)
- qidian (起点中文网)
- sfacg (SF轻小说)
- yamibo (百合会)
- common (通用架构)
"""

from .biquge import BiqugeAsyncDownloader, BiqugeDownloader
from .common import CommonAsyncDownloader, CommonDownloader
from .esjzone import EsjzoneAsyncDownloader, EsjzoneDownloader
from .qianbi import QianbiAsyncDownloader, QianbiDownloader
from .qidian import QidianDownloader
from .sfacg import SfacgAsyncDownloader, SfacgDownloader
from .yamibo import YamiboAsyncDownloader, YamiboDownloader

__all__ = [
    "BiqugeAsyncDownloader",
    "BiqugeDownloader",
    "CommonAsyncDownloader",
    "CommonDownloader",
    "EsjzoneAsyncDownloader",
    "EsjzoneDownloader",
    "QianbiAsyncDownloader",
    "QianbiDownloader",
    "QidianDownloader",
    "SfacgAsyncDownloader",
    "SfacgDownloader",
    "YamiboAsyncDownloader",
    "YamiboDownloader",
]
