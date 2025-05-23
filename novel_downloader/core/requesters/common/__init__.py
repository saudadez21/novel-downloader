#!/usr/bin/env python3
"""
novel_downloader.core.requesters.common
---------------------------------------

This module provides the `CommonSession` class wrapper for common HTTP
request operations to novel websites. It serves as a unified access
point to import `CommonSession` without exposing lower-level modules.
"""

from .async_session import CommonAsyncSession
from .session import CommonSession

__all__ = [
    "CommonAsyncSession",
    "CommonSession",
]
