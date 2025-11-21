#!/usr/bin/env python3
"""
novel_downloader.schemas
------------------------

Data contracts and type definitions.
"""

__all__ = [
    "BookConfig",
    "ClientConfig",
    "ParserConfig",
    "FetcherConfig",
    "OCRConfig",
    "ExporterConfig",
    "ProcessorConfig",
    "BookInfoDict",
    "ChapterDict",
    "ChapterInfoDict",
    "MediaResource",
    "MediaType",
    "VolumeInfoDict",
    "LoginField",
    "SearchResult",
    "ExecutedStageMeta",
    "PipelineMeta",
]

from .auth import LoginField
from .book import (
    BookInfoDict,
    ChapterDict,
    ChapterInfoDict,
    MediaResource,
    MediaType,
    VolumeInfoDict,
)
from .config import (
    BookConfig,
    ClientConfig,
    ExporterConfig,
    FetcherConfig,
    OCRConfig,
    ParserConfig,
    ProcessorConfig,
)
from .process import ExecutedStageMeta, PipelineMeta
from .search import SearchResult
