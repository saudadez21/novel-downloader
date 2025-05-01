#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.parsers
-----------------------------

This package defines all site-specific parsing modules
for the novel_downloader framework.

Currently supported:
- Qidian (起点中文网) via browser-rendered page parsing.

Modules:
- qidian_parser
- common_parser
"""

from .common_parser import CommonParser
from .qidian_parser import (
    QidianBrowserParser,
    QidianSessionParser,
)

__all__ = [
    "CommonParser",
    "QidianBrowserParser",
    "QidianSessionParser",
]
