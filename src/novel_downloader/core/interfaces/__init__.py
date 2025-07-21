#!/usr/bin/env python3
"""
novel_downloader.core.interfaces
--------------------------------

This package centralizes the protocol definitions used across the
system to promote interface-based design and type-safe dependency
injection.

Included protocols:
- DownloaderProtocol
- FetcherProtocol
- ParserProtocol
- ExporterProtocol
"""

__all__ = [
    "DownloaderProtocol",
    "ExporterProtocol",
    "FetcherProtocol",
    "ParserProtocol",
    "SearcherProtocol",
]

from .downloader import DownloaderProtocol
from .exporter import ExporterProtocol
from .fetcher import FetcherProtocol
from .parser import ParserProtocol
from .searcher import SearcherProtocol
