#!/usr/bin/env python3
"""
novel_downloader.core.parsers
-----------------------------

This package defines all site-specific parsing modules
for the novel_downloader framework.
"""

__all__ = [
    "get_parser",
    "BiqugeParser",
    "EsjzoneParser",
    "LinovelibParser",
    "QianbiParser",
    "QidianParser",
    "SfacgParser",
    "TtkanParser",
    "YamiboParser",
]

from .biquge import BiqugeParser
from .esjzone import EsjzoneParser
from .linovelib import LinovelibParser
from .qianbi import QianbiParser
from .qidian import QidianParser
from .registry import get_parser
from .sfacg import SfacgParser
from .ttkan import TtkanParser
from .yamibo import YamiboParser
