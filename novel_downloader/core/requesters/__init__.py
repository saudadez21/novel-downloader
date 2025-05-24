#!/usr/bin/env python3
"""
novel_downloader.core.requesters
--------------------------------

This package provides requester implementations for different novel platforms.
Each submodule corresponds to a specific site and encapsulates the logic needed
to perform network interactions, such as logging in, sending requests,
or interacting with browser/session-based sources.

Subpackages:
- biquge (笔趣阁)
- qianbi (铅笔小说)
- qidian (起点中文网)
- common (通用架构)
"""

from .biquge import (
    BiqugeAsyncSession,
    BiqugeSession,
)
from .common import (
    CommonAsyncSession,
    CommonSession,
)
from .qianbi import (
    QianbiAsyncSession,
    QianbiSession,
)
from .qidian import (
    QidianBrowser,
    QidianSession,
)

__all__ = [
    "BiqugeAsyncSession",
    "BiqugeSession",
    "CommonAsyncSession",
    "CommonSession",
    "QianbiAsyncSession",
    "QianbiSession",
    "QidianBrowser",
    "QidianSession",
]
