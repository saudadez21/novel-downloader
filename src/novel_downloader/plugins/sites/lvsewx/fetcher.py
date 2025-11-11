#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.lvsewx.fetcher
---------------------------------------------
"""

from typing import Any

from novel_downloader.plugins.base.fetcher import BaseFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class LvsewxFetcher(BaseFetcher):
    """
    A session class for interacting with the 绿色小说网 (www.lvsewx.cc) novel
    """

    site_name: str = "lvsewx"

    BOOK_INFO_URL = "https://www.lvsewx.cc/ebook/{bid}.html"
    CHAPTER_URL = "https://www.lvsewx.cc/books/{prefix}/{bid}/{cid}.html"

    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        url = self.BOOK_INFO_URL.format(bid=book_id)
        return [await self.fetch(url, encoding="gbk", **kwargs)]

    async def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        prefix = book_id[:-3]
        url = self.CHAPTER_URL.format(prefix=prefix, bid=book_id, cid=chapter_id)
        return [await self.fetch(url, encoding="gbk", **kwargs)]
