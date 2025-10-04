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
    "ProcessorConfig",
    "PipelineConfig",
    "BookInfoDict",
    "ChapterDict",
    "ChapterInfoDict",
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
    VolumeInfoDict,
)
from .config import (
    BookConfig,
    DownloaderConfig,
    ExporterConfig,
    FetcherConfig,
    FontOCRConfig,
    ParserConfig,
    PipelineConfig,
    ProcessorConfig,
)
from .process import ExecutedStageMeta, PipelineMeta
from .search import SearchResult
