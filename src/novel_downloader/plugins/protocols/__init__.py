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
    "ProcessorProtocol",
]

from .downloader import DownloaderProtocol
from .exporter import ExporterProtocol
from .fetcher import FetcherProtocol
from .parser import ParserProtocol
from .processor import ProcessorProtocol
