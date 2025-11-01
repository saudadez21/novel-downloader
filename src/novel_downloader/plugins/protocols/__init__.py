#!/usr/bin/env python3
"""
novel_downloader.plugins.protocols
----------------------------------

Plugin protocols defining contracts for downloader, exporter,
parser, and searcher interfaces.
"""

__all__ = [
    "ClientProtocol",
    "FetcherProtocol",
    "ParserProtocol",
    "ProcessorProtocol",
    "DownloadUI",
    "ExportUI",
    "LoginUI",
    "ProcessUI",
]

from .client import ClientProtocol
from .fetcher import FetcherProtocol
from .parser import ParserProtocol
from .processor import ProcessorProtocol
from .ui import (
    DownloadUI,
    ExportUI,
    LoginUI,
    ProcessUI,
)
