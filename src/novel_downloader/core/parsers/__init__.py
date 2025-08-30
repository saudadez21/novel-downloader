#!/usr/bin/env python3
"""
novel_downloader.core.parsers
-----------------------------

Parser implementations for extracting book metadata and
chapter content from various sources
"""

__all__ = [
    "get_parser",
    "AaatxtParser",
    "BiqugeParser",
    "BiquyueduParser",
    "DxmwxParser",
    "EightnovelParser",
    "EsjzoneParser",
    "GuidayeParser",
    "HetushuParser",
    "I25zwParser",
    "Ixdzs8Parser",
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
    "ShuhaigeParser",
    "TongrenquanParser",
    "TtkanParser",
    "WanbengoParser",
    "XiaoshuowuParser",
    "XiguashuwuParser",
    "Xs63bParser",
    "XshbookParser",
    "YamiboParser",
    "YibigeParser",
]

from .aaatxt import AaatxtParser
from .b520 import BiqugeParser
from .biquyuedu import BiquyueduParser
from .dxmwx import DxmwxParser
from .eightnovel import EightnovelParser
from .esjzone import EsjzoneParser
from .guidaye import GuidayeParser
from .hetushu import HetushuParser
from .i25zw import I25zwParser
from .ixdzs8 import Ixdzs8Parser
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
from .shuhaige import ShuhaigeParser
from .tongrenquan import TongrenquanParser
from .ttkan import TtkanParser
from .wanbengo import WanbengoParser
from .xiaoshuowu import XiaoshuowuParser
from .xiguashuwu import XiguashuwuParser
from .xs63b import Xs63bParser
from .xshbook import XshbookParser
from .yamibo import YamiboParser
from .yibige import YibigeParser
