#!/usr/bin/env python3
"""
novel_downloader.core.searchers
-------------------------------

Site-specific searcher implementations for discovering novels across multiple sources
"""

__all__ = [
    "search",
    "AaatxtSearcher",
    "BiqugeSearcher",
    "DxmwxSearcher",
    "EsjzoneSearcher",
    "HetushuSearcher",
    "I25zwSearcher",
    "Ixdzs8Searcher",
    "Jpxs123Searcher",
    "N8novelSearcher",
    "PiaotiaSearcher",
    "QbtrSearcher",
    "QianbiSearcher",
    "Quanben5Searcher",
    "ShuhaigeSearcher",
    "TongrenquanSearcher",
    "TtkanSearcher",
    "XiaoshuowuSearcher",
    "XiguashuwuSearcher",
    "Xs63bSearcher",
]

from .aaatxt import AaatxtSearcher
from .b520 import BiqugeSearcher
from .dxmwx import DxmwxSearcher
from .esjzone import EsjzoneSearcher
from .hetushu import HetushuSearcher
from .i25zw import I25zwSearcher
from .ixdzs8 import Ixdzs8Searcher
from .jpxs123 import Jpxs123Searcher
from .n8novel import N8novelSearcher
from .piaotia import PiaotiaSearcher
from .qbtr import QbtrSearcher
from .qianbi import QianbiSearcher
from .quanben5 import Quanben5Searcher
from .registry import search
from .shuhaige import ShuhaigeSearcher
from .tongrenquan import TongrenquanSearcher
from .ttkan import TtkanSearcher
from .xiaoshuowu import XiaoshuowuSearcher
from .xiguashuwu import XiguashuwuSearcher
from .xs63b import Xs63bSearcher
