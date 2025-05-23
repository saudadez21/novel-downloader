#!/usr/bin/env python3
"""
novel_downloader.core.savers
----------------------------

This module defines saver classes for different novel platforms.

Currently supported platforms:
- Biquge (笔趣阁)
- Qidian (起点中文网)
- CommonSaver (通用)
"""

from .biquge import BiqugeSaver
from .common import CommonSaver
from .qidian import QidianSaver

__all__ = [
    "BiqugeSaver",
    "CommonSaver",
    "QidianSaver",
]
