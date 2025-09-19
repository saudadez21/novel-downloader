#!/usr/bin/env python3
"""
novel_downloader.core.interfaces
--------------------------------

Protocol interfaces defining the contracts for core components.
"""

__all__ = [
    "DownloaderProtocol",
    "ExporterProtocol",
    "FetcherProtocol",
    "ParserProtocol",
]

from .downloader import DownloaderProtocol
from .exporter import ExporterProtocol
from .fetcher import FetcherProtocol
from .parser import ParserProtocol
