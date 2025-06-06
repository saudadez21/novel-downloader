#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.common
-------------------------------------

"""

from .browser import CommonBrowser
from .session import CommonSession

__all__ = [
    "CommonBrowser",
    "CommonSession",
]
