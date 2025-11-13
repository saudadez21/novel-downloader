#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.wenku8.fetcher
---------------------------------------------
"""

import asyncio
from typing import Any

from novel_downloader.plugins.base.fetcher import BaseFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class Wenku8Fetcher(BaseFetcher):
    """
    A session class for interacting with the 轻小说文库 (www.wenku8.net) novel.
    """

    site_name: str = "wenku8"

    BOOK_INFO_URL = "https://www.wenku8.net/book/{bid}.htm"
    BOOK_CATALOG_URL = "https://www.wenku8.net/novel/{prefix}/{bid}/index.htm"
    CHAPTER_URL = "https://www.wenku8.net/novel/{prefix}/{bid}/{cid}.htm"

    async def fetch_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        prefix = self._compute_prefix(book_id)

        info_url = self.BOOK_INFO_URL.format(bid=book_id)
        catalog_url = self.BOOK_CATALOG_URL.format(prefix=prefix, bid=book_id)

        info_resp, catalog_resp = await asyncio.gather(
            self.fetch(info_url, **kwargs),
            self.fetch(catalog_url, **kwargs),
        )
        return [info_resp, catalog_resp]

    async def fetch_chapter_content(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        prefix = self._compute_prefix(book_id)
        url = self.CHAPTER_URL.format(prefix=prefix, bid=book_id, cid=chapter_id)
        return [await self.fetch(url, **kwargs)]

    @staticmethod
    def _compute_prefix(book_id: str) -> str:
        # Wenku8 rule: IDs < 1000 placed in directory 0
        return "0" if len(book_id) <= 3 else book_id[:-3]
