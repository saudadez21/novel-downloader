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

    BOOK_INFO_URL = "https://www.wenku8.net/book/{book_num}.htm"
    BOOK_CATALOG_URL = "https://www.wenku8.net/novel/{book_path}/index.htm"
    CHAPTER_URL = "https://www.wenku8.net/novel/{book_id}/{chapter_id}.htm"

    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        parts = book_id.split("-")
        if len(parts) != 2:
            raise ValueError(f"Invalid book_id format: {book_id}")

        group_id, book_num = parts
        book_path = f"{group_id}/{book_num}"

        info_url = self.BOOK_INFO_URL.format(book_num=book_num)
        catalog_url = self.BOOK_CATALOG_URL.format(book_path=book_path)

        info_resp, catalog_resp = await asyncio.gather(
            self.fetch(info_url, **kwargs),
            self.fetch(catalog_url, **kwargs),
        )
        return [info_resp, catalog_resp]

    async def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        book_id = book_id.replace("-", "/")
        url = self.CHAPTER_URL.format(book_id=book_id, chapter_id=chapter_id)
        return [await self.fetch(url, **kwargs)]
