#!/usr/bin/env python3
"""
novel_downloader.models
-----------------------

Data models and configuration classes.
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
from .login import LoginField
from .search import SearchResult
