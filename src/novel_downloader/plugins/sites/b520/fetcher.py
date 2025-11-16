#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.b520.fetcher
-------------------------------------------

"""

import logging
from typing import Any

from novel_downloader.plugins.base.fetcher import BaseFetcher
from novel_downloader.plugins.registry import registrar

logger = logging.getLogger(__name__)


@registrar.register_fetcher()
class B520Fetcher(BaseFetcher):
    """
    A session class for interacting with the 笔趣阁 (www.b520.cc) novel.
    """

    site_name: str = "b520"

    BOOK_INFO_URL = "http://www.b520.cc/{book_id}/"
    CHAPTER_URL = "http://www.b520.cc/{book_id}/{chapter_id}.html"

    IMAGE_HEADERS = {**BaseFetcher.IMAGE_HEADERS, "Referer": "http://www.b520.cc/"}

    async def fetch_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        headers = {
            **self.headers,
            "Referer": "http://www.b520.cc/",
        }
        url = self.book_info_url(book_id=book_id)
        return [await self.fetch(url, headers=headers, **kwargs)]

    async def fetch_chapter_content(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        headers = {
            **self.headers,
            "Referer": "http://www.b520.cc/",
        }
        url = self.chapter_url(book_id=book_id, chapter_id=chapter_id)
        return [await self.fetch(url, headers=headers, encoding="gbk", **kwargs)]

    @classmethod
    def book_info_url(cls, book_id: str) -> str:
        return cls.BOOK_INFO_URL.format(book_id=book_id)

    @classmethod
    def chapter_url(cls, book_id: str, chapter_id: str) -> str:
        return cls.CHAPTER_URL.format(book_id=book_id, chapter_id=chapter_id)
