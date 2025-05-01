#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.parsers.qidian_parser
-------------------------------------------

This package provides parsing implementations for the Qidian platform.

Modules:
- browser: Contains `QidianBrowserParser` for browser-rendered page parsing.
- session: Contains `QidianSessionParser` for session page parsing.
"""

from .browser import QidianBrowserParser
from .session import QidianSessionParser

__all__ = [
    "QidianBrowserParser",
    "QidianSessionParser",
]
