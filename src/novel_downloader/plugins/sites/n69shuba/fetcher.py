#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n69shuba.fetcher
-----------------------------------------------
"""

import asyncio
from typing import Any

from novel_downloader.plugins.base.fetcher import BaseFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class N69shubaFetcher(BaseFetcher):
    """
    A session class for interacting with the 69书吧 (www.69shuba.com) novel.
    """

    site_name: str = "n69shuba"

    HAS_SEPARATE_CATALOG: bool = True
    BOOK_INFO_URL = "https://www.69shuba.com/book/{book_id}.htm"
    BOOK_CATALOG_URL = "https://www.69shuba.com/book/{book_id}/"
    CHAPTER_URL = "https://www.69shuba.com/txt/{book_id}/{chapter_id}"

    async def get_book_info(self, book_id: str, **kwargs: Any) -> list[str]:
        headers = {
            **self.headers,
            "Referer": "https://www.69shuba.com/",
        }

        info_url = self.BOOK_INFO_URL.format(book_id=book_id)
        catalog_url = self.BOOK_CATALOG_URL.format(book_id=book_id)

        info_resp, catalog_resp = await asyncio.gather(
            self.fetch(info_url, headers=headers, **kwargs),
            self.fetch(catalog_url, headers=headers, **kwargs),
        )
        return [info_resp, catalog_resp]

    async def get_book_chapter(
        self, book_id: str, chapter_id: str, **kwargs: Any
    ) -> list[str]:
        headers = {
            **self.headers,
            "Referer": f"https://www.69shuba.com/book/{chapter_id}/",
        }
        url = self.CHAPTER_URL.format(book_id=book_id, chapter_id=chapter_id)
        return [await self.fetch(url, headers=headers, **kwargs)]
