#!/usr/bin/env python3
"""
novel_downloader.core.searchers
-------------------------------

"""

__all__ = [
    "search",
    "BiqugeSearcher",
    "EightnovelSearcher",
    "EsjzoneSearcher",
    "HetushuSearcher",
    "I25zwSearcher",
    "PiaotiaSearcher",
    "QbtrSearcher",
    "QianbiSearcher",
    "Quanben5Searcher",
    "TongrenquanSearcher",
    "TtkanSearcher",
    "XiaoshuowuSearcher",
]

from .biquge import BiqugeSearcher
from .eightnovel import EightnovelSearcher
from .esjzone import EsjzoneSearcher
from .hetushu import HetushuSearcher
from .i25zw import I25zwSearcher
from .piaotia import PiaotiaSearcher
from .qbtr import QbtrSearcher
from .qianbi import QianbiSearcher
from .quanben5 import Quanben5Searcher
from .registry import search
from .tongrenquan import TongrenquanSearcher
from .ttkan import TtkanSearcher
from .xiaoshuowu import XiaoshuowuSearcher
