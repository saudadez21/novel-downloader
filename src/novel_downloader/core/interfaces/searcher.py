#!/usr/bin/env python3
"""
novel_downloader.core.interfaces.searcher
-----------------------------------------

"""

from typing import Protocol

from novel_downloader.models import SearchResult


class SearcherProtocol(Protocol):
    site_name: str

    @classmethod
    def search(cls, keyword: str, limit: int | None = None) -> list[SearchResult]:
        ...
