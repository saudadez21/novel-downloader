#!/usr/bin/env python3
"""
novel_downloader.apps.web.pages
-------------------------------

Page definitions for the web interface. Each file corresponds to a feature page.
"""

__all__ = [
    "page_download",  # /download
    "page_history",  # /history
    "page_progress",  # /progress
    "page_search",  # /
]

from .download import page_download
from .history import page_history
from .progress import page_progress
from .search import page_search
