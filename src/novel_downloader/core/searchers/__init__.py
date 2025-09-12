#!/usr/bin/env python3
"""
novel_downloader.core.searchers
-------------------------------

Site-specific searcher implementations for discovering novels across multiple sources
"""

__all__ = ["search", "search_stream"]

from .registry import search, search_stream
