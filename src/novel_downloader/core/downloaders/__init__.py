#!/usr/bin/env python3
"""
novel_downloader.core.downloaders
---------------------------------

Downloader implementations for retrieving novels from different sources
"""

__all__ = ["get_downloader"]

from .registry import get_downloader
