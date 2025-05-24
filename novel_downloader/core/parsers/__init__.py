#!/usr/bin/env python3
"""
novel_downloader.core.parsers
-----------------------------

This package defines all site-specific parsing modules
for the novel_downloader framework.

Modules:
- biquge (笔趣阁)
- qianbi (铅笔小说)
- qidian (起点中文网)
- common (通用架构)
"""

from .biquge import BiqugeParser
from .common import CommonParser
from .qianbi import QianbiParser
from .qidian import (
    QidianBrowserParser,
    QidianSessionParser,
)

__all__ = [
    "BiqugeParser",
    "CommonParser",
    "QianbiParser",
    "QidianBrowserParser",
    "QidianSessionParser",
]
