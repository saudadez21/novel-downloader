#!/usr/bin/env python3
"""
novel_downloader.plugins.protocols
----------------------------------

Plugin protocols defining contracts for downloader, exporter,
parser, and searcher interfaces.
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
