#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.twkan.fetcher
--------------------------------------------
"""


import asyncio
from typing import Any

from novel_downloader.plugins.base.fetcher import BaseFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class TwkanFetcher(BaseFetcher):
    """
    A session class for interacting with the 台灣小說網 (twkan.com) novel.
    """

    site_name: str = "twkan"

    HAS_SEPARATE_CATALOG: bool = True
    BOOK_INFO_URL = "https://twkan.com/book/{book_id}.html"
    BOOK_CATALOG_URL = "https://twkan.com/ajax_novels/chapterlist/{book_id}.html"
    CHAPTER_URL = "https://twkan.com/txt/{book_id}/{chapter_id}"

    async def get_book_info(self, book_id: str, **kwargs: Any) -> list[str]:
        info_headers = {
            **self.headers,
            "Referer": "https://twkan.com/",
        }
        cata_headers = {
            **self.headers,
            "Referer": f"https://twkan.com/book/{book_id}/index.html",
        }

        info_url = self.BOOK_INFO_URL.format(book_id=book_id)
        catalog_url = self.BOOK_CATALOG_URL.format(book_id=book_id)

        info_resp, catalog_resp = await asyncio.gather(
            self.fetch(info_url, headers=info_headers, **kwargs),
            self.fetch(catalog_url, headers=cata_headers, **kwargs),
        )
        return [info_resp, catalog_resp]

    async def get_book_chapter(
        self, book_id: str, chapter_id: str, **kwargs: Any
    ) -> list[str]:
        headers = {
            **self.headers,
            "Referer": f"https://twkan.com/book/{chapter_id}/index.html",
        }
        url = self.CHAPTER_URL.format(book_id=book_id, chapter_id=chapter_id)
        return [await self.fetch(url, headers=headers, **kwargs)]
