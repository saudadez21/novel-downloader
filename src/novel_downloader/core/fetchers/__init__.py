#!/usr/bin/env python3
"""
novel_downloader.core.fetchers
------------------------------

Fetcher implementations for retrieving raw data and HTML from various novel sources
"""

__all__ = ["get_fetcher"]

from .registry import get_fetcher
