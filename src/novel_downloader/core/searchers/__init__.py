#!/usr/bin/env python3
"""
novel_downloader.core.searchers
-------------------------------

"""

__all__ = [
    "search",
    "BiqugeSearcher",
    "EsjzoneSearcher",
    "QianbiSearcher",
    "QidianSearcher",
]

from .biquge import BiqugeSearcher
from .esjzone import EsjzoneSearcher
from .qianbi import QianbiSearcher
from .qidian import QidianSearcher
from .registry import search
