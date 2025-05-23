#!/usr/bin/env python3
"""
novel_downloader.core.requesters.base
-------------------------------------

"""

from .async_session import BaseAsyncSession
from .browser import BaseBrowser
from .session import BaseSession

__all__ = [
    "BaseAsyncSession",
    "BaseBrowser",
    "BaseSession",
]
