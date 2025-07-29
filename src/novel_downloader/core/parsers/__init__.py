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
    "BiquyueduParser",
    "EsjzoneParser",
    "GuidayeParser",
    "HetushuParser",
    "I25zwParser",
    "LinovelibParser",
    "PiaotiaParser",
    "QianbiParser",
    "QidianParser",
    "Quanben5Parser",
    "SfacgParser",
    "TtkanParser",
    "XiaoshuowuParser",
    "YamiboParser",
]

from .biquge import BiqugeParser
from .biquyuedu import BiquyueduParser
from .esjzone import EsjzoneParser
from .guidaye import GuidayeParser
from .hetushu import HetushuParser
from .i25zw import I25zwParser
from .linovelib import LinovelibParser
from .piaotia import PiaotiaParser
from .qianbi import QianbiParser
from .qidian import QidianParser
from .quanben5 import Quanben5Parser
from .registry import get_parser
from .sfacg import SfacgParser
from .ttkan import TtkanParser
from .xiaoshuowu import XiaoshuowuParser
from .yamibo import YamiboParser
