#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.tianyabooks.fetcher
--------------------------------------------------
"""

from typing import Any

from novel_downloader.plugins.base.fetcher import BaseFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class TianyabooksFetcher(BaseFetcher):
    """
    A session class for interacting with the 天涯书库 (www.tianyabooks.com) novel
    """

    site_name: str = "tianyabooks"

    BOOK_ID_REPLACEMENTS = [("-", "/")]

    BOOK_INFO_URL = "https://www.tianyabooks.com/{book_id}/"
    CHAPTER_URL = "https://www.tianyabooks.com/{book_id}/{chapter_id}.html"

    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        book_id = book_id.replace("-", "/")
        url = self.BOOK_INFO_URL.format(book_id=book_id)
        return [await self.fetch(url, encoding="gbk", **kwargs)]

    async def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        book_id = book_id.replace("-", "/")
        url = self.CHAPTER_URL.format(book_id=book_id, chapter_id=chapter_id)
        return [await self.fetch(url, encoding="gbk", **kwargs)]
