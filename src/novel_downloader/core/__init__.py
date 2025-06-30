#!/usr/bin/env python3
"""
novel_downloader.core
---------------------

This package serves as the core layer of the novel_downloader system.

It provides factory methods for constructing key components required for
downloading and processing online novel content, including:

- Downloader: Handles the full download lifecycle of a book or a batch of books.
- Parser: Extracts structured data from HTML or SSR content.
- Fetcher: Sends HTTP requests and manages sessions, including login if required.
- Exporter: Responsible for exporting downloaded data into various output formats.
"""

from .factory import (
    get_downloader,
    get_exporter,
    get_fetcher,
    get_parser,
)
from .interfaces import (
    DownloaderProtocol,
    ExporterProtocol,
    FetcherProtocol,
    ParserProtocol,
)

__all__ = [
    "get_downloader",
    "get_exporter",
    "get_fetcher",
    "get_parser",
    "DownloaderProtocol",
    "ExporterProtocol",
    "FetcherProtocol",
    "ParserProtocol",
]
