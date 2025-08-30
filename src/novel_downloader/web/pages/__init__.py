#!/usr/bin/env python3
"""
novel_downloader.web.pages
--------------------------

NiceGUI page registrations; importing this package exposes and registers all routes.
"""

__all__ = [
    "page_download",  # /download
    "page_progress",  # /progress
    "page_search",  # /
]

from .download import page_download
from .progress import page_progress
from .search import page_search
