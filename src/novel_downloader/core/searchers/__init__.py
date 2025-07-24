#!/usr/bin/env python3
"""
novel_downloader.core.searchers
-------------------------------

"""

__all__ = [
    "search",
    "BiqugeSearcher",
    "EsjzoneSearcher",
    "PiaotiaSearcher",
    "QianbiSearcher",
    "QidianSearcher",
    "TtkanSearcher",
]

from .biquge import BiqugeSearcher
from .esjzone import EsjzoneSearcher
from .piaotia import PiaotiaSearcher
from .qianbi import QianbiSearcher
from .qidian import QidianSearcher
from .registry import search
from .ttkan import TtkanSearcher
