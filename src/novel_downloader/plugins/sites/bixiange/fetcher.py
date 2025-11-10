#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.bixiange.fetcher
-----------------------------------------------
"""

from typing import Any

from novel_downloader.plugins.base.fetcher import BaseFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class BixiangeFetcher(BaseFetcher):
    """
    A session class for interacting with the 笔仙阁 (m.bixiange.me) novel
    """

    site_name: str = "bixiange"

    INFO_HTML_SUFFIX = {"cyjk", "khjj", "guanchang"}
    CHAPTER_NO_INDEX = {"cyjk", "khjj", "guanchang"}

    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        book_id = book_id.replace("-", "/")
        prefix = book_id.split("/")[0]

        if prefix in self.INFO_HTML_SUFFIX:
            url = f"https://m.bixiange.me/{book_id}.html"
        else:
            url = f"https://m.bixiange.me/{book_id}/"

        return [await self.fetch(url, **kwargs)]

    async def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        book_id = book_id.replace("-", "/")
        prefix = book_id.split("/")[0]

        if prefix in self.CHAPTER_NO_INDEX:
            url = f"https://m.bixiange.me/{book_id}/{chapter_id}.html"
        else:
            url = f"https://m.bixiange.me/{book_id}/index/{chapter_id}.html"

        return [await self.fetch(url, **kwargs)]
