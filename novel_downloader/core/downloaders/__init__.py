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
- linovelib (哔哩轻小说)
- qianbi (铅笔小说)
- qidian (起点中文网)
- sfacg (SF轻小说)
- yamibo (百合会)
- common (通用架构)
"""

from .biquge import BiqugeDownloader
from .common import CommonDownloader
from .esjzone import EsjzoneDownloader
from .linovelib import LinovelibDownloader
from .qianbi import QianbiDownloader
from .qidian import QidianDownloader
from .sfacg import SfacgDownloader
from .yamibo import YamiboDownloader

__all__ = [
    "BiqugeDownloader",
    "EsjzoneDownloader",
    "LinovelibDownloader",
    "QianbiDownloader",
    "QidianDownloader",
    "SfacgDownloader",
    "YamiboDownloader",
    "CommonDownloader",
]
