#!/usr/bin/env python3
"""
novel_downloader.plugins
------------------------
"""

__all__ = [
    "registrar",
    "DownloaderProtocol",
    "ExporterProtocol",
    "FetcherProtocol",
    "ParserProtocol",
]

from .protocols import (
    DownloaderProtocol,
    ExporterProtocol,
    FetcherProtocol,
    ParserProtocol,
)
from .registry import registrar
