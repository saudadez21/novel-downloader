#!/usr/bin/env python3
"""
novel_downloader.schemas
------------------------

Data contracts and type definitions.
"""

__all__ = [
    "BookConfig",
    "DownloaderConfig",
    "ParserConfig",
    "FetcherConfig",
    "FontOCRConfig",
    "ExporterConfig",
    "TextCleanerConfig",
    "BookInfoDict",
    "ChapterDict",
    "ChapterInfoDict",
    "VolumeInfoDict",
    "LoginField",
    "SearchResult",
]

from .auth import LoginField
from .book import (
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    VolumeInfoDict,
)
from .config import (
    BookConfig,
    DownloaderConfig,
    ExporterConfig,
    FetcherConfig,
    FontOCRConfig,
    ParserConfig,
    TextCleanerConfig,
)
from .search import SearchResult
