#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.b520
-----------------------------------

"""

from typing import Any

from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["b520"],
)
class B520Session(GenericSession):
    """
    A session class for interacting with the 笔趣阁 (www.b520.cc) novel.
    """

    site_name: str = "b520"

    BOOK_INFO_URL = "http://www.b520.cc/{book_id}/"
    CHAPTER_URL = "http://www.b520.cc/{book_id}/{chapter_id}.html"

    async def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        url = self.chapter_url(book_id=book_id, chapter_id=chapter_id)
        return [await self.fetch(url, encoding="gbk", **kwargs)]
