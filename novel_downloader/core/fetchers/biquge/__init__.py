#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.biquge
-------------------------------------

"""

from .browser import BiqugeBrowser
from .session import BiqugeSession

__all__ = [
    "BiqugeBrowser",
    "BiqugeSession",
]
