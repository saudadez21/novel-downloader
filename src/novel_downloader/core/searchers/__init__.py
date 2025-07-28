#!/usr/bin/env python3
"""
novel_downloader.core.searchers
-------------------------------

"""

__all__ = [
    "search",
    "BiqugeSearcher",
    "EsjzoneSearcher",
    "HetushuSearcher",
    "I25zwSearcher",
    "PiaotiaSearcher",
    "QianbiSearcher",
    "QidianSearcher",
    "Quanben5Searcher",
    "TtkanSearcher",
    "XiaoshuowuSearcher",
]

from .biquge import BiqugeSearcher
from .esjzone import EsjzoneSearcher
from .hetushu import HetushuSearcher
from .i25zw import I25zwSearcher
from .piaotia import PiaotiaSearcher
from .qianbi import QianbiSearcher
from .qidian import QidianSearcher
from .quanben5 import Quanben5Searcher
from .registry import search
from .ttkan import TtkanSearcher
from .xiaoshuowu import XiaoshuowuSearcher
