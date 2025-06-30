#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.base
-----------------------------------

"""

from .browser import BaseBrowser
from .session import BaseSession

__all__ = [
    "BaseBrowser",
    "BaseSession",
]
