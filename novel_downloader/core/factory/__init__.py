#!/usr/bin/env python3
"""
novel_downloader.core.factory
-----------------------------

This package provides factory methods for dynamically retrieving components
based on runtime parameters such as site name or content type.
"""

from .downloader import get_downloader
from .exporter import get_exporter
from .fetcher import get_fetcher
from .parser import get_parser

__all__ = [
    "get_downloader",
    "get_exporter",
    "get_fetcher",
    "get_parser",
]
