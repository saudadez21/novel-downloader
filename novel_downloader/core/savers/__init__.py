#!/usr/bin/env python3
"""
novel_downloader.core.savers
----------------------------

This module defines saver classes for different novel platforms.

Currently supported platforms:
- biquge (笔趣阁)
- qianbi (铅笔小说)
- qidian (起点中文网)
- sfacg (SF轻小说)
- common (通用架构)
"""

from .biquge import BiqugeSaver
from .common import CommonSaver
from .qianbi import QianbiSaver
from .qidian import QidianSaver
from .sfacg import SfacgSaver

__all__ = [
    "BiqugeSaver",
    "CommonSaver",
    "QianbiSaver",
    "QidianSaver",
    "SfacgSaver",
]
