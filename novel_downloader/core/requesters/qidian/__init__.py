#!/usr/bin/env python3
"""
novel_downloader.core.requesters.qidian
---------------------------------------

This package provides the implementation of the Qidian-specific requester logic.
It contains modules for interacting with Qidian's website, including login,
page navigation, and data retrieval using a browser-based automation approach.

Modules:
- browser
- session
"""

from .broswer import QidianBrowser
from .session import QidianSession

__all__ = [
    "QidianBrowser",
    "QidianSession",
]
