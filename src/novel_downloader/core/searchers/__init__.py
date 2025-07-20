#!/usr/bin/env python3
"""
novel_downloader.core.searchers
-------------------------------

"""

__all__ = [
    "search",
    "QidianSearcher",
]

from .qidian import QidianSearcher
from .registry import search
