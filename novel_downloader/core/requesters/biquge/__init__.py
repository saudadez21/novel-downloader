#!/usr/bin/env python3
"""
novel_downloader.core.requesters.biquge
---------------------------------------

"""

from .async_session import BiqugeAsyncSession
from .session import BiqugeSession

__all__ = [
    "BiqugeAsyncSession",
    "BiqugeSession",
]
