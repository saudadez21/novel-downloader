#!/usr/bin/env python3
"""
novel_downloader.core.parsers
-----------------------------

This package defines all site-specific parsing modules
for the novel_downloader framework.

Currently supported:
- Qidian (起点中文网)

Modules:
- qidian_parser
- common_parser
"""

from .biquge import BiqugeParser
from .common import CommonParser
from .qidian import (
    QidianBrowserParser,
    QidianSessionParser,
)

__all__ = [
    "BiqugeParser",
    "CommonParser",
    "QidianBrowserParser",
    "QidianSessionParser",
]
