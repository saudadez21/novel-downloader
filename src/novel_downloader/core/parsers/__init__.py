#!/usr/bin/env python3
"""
novel_downloader.core.parsers
-----------------------------

This package defines all site-specific parsing modules
for the novel_downloader framework.
"""

__all__ = [
    "get_parser",
    "AaatxtParser",
    "BiqugeParser",
    "BiquyueduParser",
    "DeqixsParser",
    "EightnovelParser",
    "EsjzoneParser",
    "GuidayeParser",
    "HetushuParser",
    "I25zwParser",
    "Jpxs123Parser",
    "LewennParser",
    "LinovelibParser",
    "PiaotiaParser",
    "QbtrParser",
    "QianbiParser",
    "QidianParser",
    "Quanben5Parser",
    "SfacgParser",
    "ShencouParser",
    "TongrenquanParser",
    "TtkanParser",
    "XiaoshuowuParser",
    "XiguashuwuParser",
    "YamiboParser",
]

from .aaatxt import AaatxtParser
from .biquge import BiqugeParser
from .biquyuedu import BiquyueduParser
from .deqixs import DeqixsParser
from .eightnovel import EightnovelParser
from .esjzone import EsjzoneParser
from .guidaye import GuidayeParser
from .hetushu import HetushuParser
from .i25zw import I25zwParser
from .jpxs123 import Jpxs123Parser
from .lewenn import LewennParser
from .linovelib import LinovelibParser
from .piaotia import PiaotiaParser
from .qbtr import QbtrParser
from .qianbi import QianbiParser
from .qidian import QidianParser
from .quanben5 import Quanben5Parser
from .registry import get_parser
from .sfacg import SfacgParser
from .shencou import ShencouParser
from .tongrenquan import TongrenquanParser
from .ttkan import TtkanParser
from .xiaoshuowu import XiaoshuowuParser
from .xiguashuwu import XiguashuwuParser
from .yamibo import YamiboParser
