#!/usr/bin/env python3
"""
novel_downloader.core.parsers
-----------------------------

This package defines all site-specific parsing modules
for the novel_downloader framework.

Modules:
- biquge (笔趣阁)
- esjzone (ESJ Zone)
- qianbi (铅笔小说)
- qidian (起点中文网)
- sfacg (SF轻小说)
- yamibo (百合会)
- common (通用架构)
"""

from .biquge import BiqugeParser
from .common import CommonParser
from .esjzone import EsjzoneParser
from .qianbi import QianbiParser
from .qidian import (
    QidianBrowserParser,
    QidianSessionParser,
)
from .sfacg import SfacgParser
from .yamibo import YamiboParser

__all__ = [
    "BiqugeParser",
    "CommonParser",
    "EsjzoneParser",
    "QianbiParser",
    "QidianBrowserParser",
    "QidianSessionParser",
    "SfacgParser",
    "YamiboParser",
]
