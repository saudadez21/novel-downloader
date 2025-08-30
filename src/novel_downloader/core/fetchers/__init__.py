#!/usr/bin/env python3
"""
novel_downloader.core.fetchers
------------------------------

Fetcher implementations for retrieving raw data and HTML from various novel sources
"""

__all__ = [
    "get_fetcher",
    "AaatxtSession",
    "BiqugeSession",
    "BiquyueduSession",
    "DxmwxSession",
    "EightnovelSession",
    "EsjzoneSession",
    "GuidayeSession",
    "HetushuSession",
    "I25zwSession",
    "Ixdzs8Session",
    "Jpxs123Session",
    "LewennSession",
    "LinovelibSession",
    "PiaotiaSession",
    "QbtrSession",
    "QianbiSession",
    "QidianSession",
    "Quanben5Session",
    "SfacgSession",
    "ShencouSession",
    "ShuhaigeSession",
    "TongrenquanSession",
    "TtkanSession",
    "WanbengoSession",
    "XiaoshuowuSession",
    "XiguashuwuSession",
    "Xs63bSession",
    "XshbookSession",
    "YamiboSession",
    "YibigeSession",
]

from .aaatxt import AaatxtSession
from .b520 import BiqugeSession
from .biquyuedu import BiquyueduSession
from .dxmwx import DxmwxSession
from .eightnovel import EightnovelSession
from .esjzone import EsjzoneSession
from .guidaye import GuidayeSession
from .hetushu import HetushuSession
from .i25zw import I25zwSession
from .ixdzs8 import Ixdzs8Session
from .jpxs123 import Jpxs123Session
from .lewenn import LewennSession
from .linovelib import LinovelibSession
from .piaotia import PiaotiaSession
from .qbtr import QbtrSession
from .qianbi import QianbiSession
from .qidian import QidianSession
from .quanben5 import Quanben5Session
from .registry import get_fetcher
from .sfacg import SfacgSession
from .shencou import ShencouSession
from .shuhaige import ShuhaigeSession
from .tongrenquan import TongrenquanSession
from .ttkan import TtkanSession
from .wanbengo import WanbengoSession
from .xiaoshuowu import XiaoshuowuSession
from .xiguashuwu import XiguashuwuSession
from .xs63b import Xs63bSession
from .xshbook import XshbookSession
from .yamibo import YamiboSession
from .yibige import YibigeSession
