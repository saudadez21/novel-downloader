#!/usr/bin/env python3
"""
novel_downloader.core.interfaces.searcher
-----------------------------------------

Protocol defining the interface for site search implementations.
"""

from typing import Protocol

import aiohttp

from novel_downloader.models import SearchResult


class SearcherProtocol(Protocol):
    site_name: str

    @classmethod
    def configure(cls, session: aiohttp.ClientSession) -> None:
        """Configure the shared session"""
        ...

    @classmethod
    async def search(cls, keyword: str, limit: int | None = None) -> list[SearchResult]:
        ...
