#!/usr/bin/env python3
"""
novel_downloader.core.requesters
--------------------------------

This package provides requester implementations for different novel platforms.
Each submodule corresponds to a specific site and encapsulates the logic needed
to perform network interactions, such as logging in, sending requests,
or interacting with browser/session-based sources.

Subpackages:
- common
- biquge
- qidian
"""

from .biquge import (
    BiqugeSession,
)
from .common import (
    CommonAsyncSession,
    CommonSession,
)
from .qidian import (
    QidianBrowser,
    QidianSession,
)

__all__ = [
    "BiqugeSession",
    "CommonAsyncSession",
    "CommonSession",
    "QidianBrowser",
    "QidianSession",
]
