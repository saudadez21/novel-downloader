#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.requesters.qidian_requester
-------------------------------------------------

This package provides the implementation of the Qidian-specific requester logic.
It contains modules for interacting with Qidian's website, including login,
page navigation, and data retrieval using a browser-based automation approach.

Modules:
- qidian_browser: Implements the QidianBrowser class for automated browser control.
- qidian_session: Implements the QidianSession class.
"""

from .qidian_broswer import QidianBrowser
from .qidian_session import QidianSession

__all__ = [
    "QidianBrowser",
    "QidianSession",
]
