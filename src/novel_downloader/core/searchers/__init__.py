#!/usr/bin/env python3
"""
novel_downloader.core.searchers
-------------------------------

"""

__all__ = [
    "search",
    "AaatxtSearcher",
    "BiqugeSearcher",
    "DxmwxSearcher",
    "EightnovelSearcher",
    "EsjzoneSearcher",
    "HetushuSearcher",
    "I25zwSearcher",
    "Ixdzs8Searcher",
    "Jpxs123Searcher",
    "PiaotiaSearcher",
    "QbtrSearcher",
    "QianbiSearcher",
    "Quanben5Searcher",
    "ShuhaigeSearcher",
    "TongrenquanSearcher",
    "TtkanSearcher",
    "WanbengoSearcher",
    "XiaoshuowuSearcher",
    "XiguashuwuSearcher",
    "Xs63bSearcher",
    "XshbookSearcher",
]

from .aaatxt import AaatxtSearcher
from .biquge import BiqugeSearcher
from .dxmwx import DxmwxSearcher
from .eightnovel import EightnovelSearcher
from .esjzone import EsjzoneSearcher
from .hetushu import HetushuSearcher
from .i25zw import I25zwSearcher
from .ixdzs8 import Ixdzs8Searcher
from .jpxs123 import Jpxs123Searcher
from .piaotia import PiaotiaSearcher
from .qbtr import QbtrSearcher
from .qianbi import QianbiSearcher
from .quanben5 import Quanben5Searcher
from .registry import search
from .shuhaige import ShuhaigeSearcher
from .tongrenquan import TongrenquanSearcher
from .ttkan import TtkanSearcher
from .wanbengo import WanbengoSearcher
from .xiaoshuowu import XiaoshuowuSearcher
from .xiguashuwu import XiguashuwuSearcher
from .xs63b import Xs63bSearcher
from .xshbook import XshbookSearcher
