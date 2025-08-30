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
- search: Provides unified search functionality across supported novel sites.
"""

__all__ = [
    "get_downloader",
    "get_exporter",
    "get_fetcher",
    "get_parser",
    "search",
    "DownloaderProtocol",
    "ExporterProtocol",
    "FetcherProtocol",
    "ParserProtocol",
]

from .downloaders import get_downloader
from .exporters import get_exporter
from .fetchers import get_fetcher
from .interfaces import (
    DownloaderProtocol,
    ExporterProtocol,
    FetcherProtocol,
    ParserProtocol,
)
from .parsers import get_parser
from .searchers import search
