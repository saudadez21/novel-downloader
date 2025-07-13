#!/usr/bin/env python3
"""
novel_downloader.core.parsers
-----------------------------

This package defines all site-specific parsing modules
for the novel_downloader framework.

Modules:
- biquge (笔趣阁)
- esjzone (ESJ Zone)
- linovelib (哔哩轻小说)
- qianbi (铅笔小说)
- qidian (起点中文网)
- sfacg (SF轻小说)
- yamibo (百合会)
"""

__all__ = [
    "get_parser",
    "BiqugeParser",
    "EsjzoneParser",
    "LinovelibParser",
    "QianbiParser",
    "QidianParser",
    "SfacgParser",
    "YamiboParser",
]

from .biquge import BiqugeParser
from .esjzone import EsjzoneParser
from .linovelib import LinovelibParser
from .qianbi import QianbiParser
from .qidian import QidianParser
from .registry import get_parser
from .sfacg import SfacgParser
from .yamibo import YamiboParser
