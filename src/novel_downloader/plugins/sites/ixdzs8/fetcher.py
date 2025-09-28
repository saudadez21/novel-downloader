#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ixdzs8.fetcher
---------------------------------------------

"""

import asyncio
import re
from typing import Any

from novel_downloader.plugins.base.fetcher import BaseSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class Ixdzs8Session(BaseSession):
    """
    A session class for interacting with the 爱下电子书 (ixdzs8.com) novel.
    """

    site_name: str = "ixdzs8"

    BOOK_INFO_URL = "https://ixdzs8.com/read/{book_id}/"
    BOOK_CATALOG_URL = "https://ixdzs8.com/novel/clist/"
    CHAPTER_URL = "https://ixdzs8.com/read/{book_id}/{chapter_id}.html"
    _TOKEN_PATTERN = re.compile(r'let\s+token\s*=\s*"([^"]+)"')

    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML of the book info page asynchronously.

        Order: [info, catalog]

        :param book_id: The book identifier.
        :return: The page content as string list.
        """
        url = self.book_info_url(book_id=book_id)
        data = {"bid": book_id}
        info_html, clist_response = await asyncio.gather(
            self.fetch_verified_html(url, **kwargs),
            self.post(self.BOOK_CATALOG_URL, data),
        )
        catalog_html = await clist_response.text()
        return [info_html, catalog_html]

    async def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        url = self.chapter_url(book_id=book_id, chapter_id=chapter_id)
        return [await self.fetch_verified_html(url, **kwargs)]

    @classmethod
    def book_info_url(cls, book_id: str) -> str:
        """
        Construct the URL for fetching a book's info page.

        :param book_id: The identifier of the book.
        :return: Fully qualified URL for the book info page.
        """
        return cls.BOOK_INFO_URL.format(book_id=book_id)

    @classmethod
    def chapter_url(cls, book_id: str, chapter_id: str) -> str:
        """
        Construct the URL for fetching a specific chapter.

        :param book_id: The identifier of the book.
        :param chapter_id: The identifier of the chapter.
        :return: Fully qualified chapter URL.
        """
        return cls.CHAPTER_URL.format(book_id=book_id, chapter_id=chapter_id)

    async def fetch_verified_html(self, url: str, **kwargs: Any) -> str:
        """
        Automatically solving the browser verification challenge if required.
        """
        resp = await self.fetch(url, **kwargs)

        if "正在验证浏览器" not in resp:
            return resp

        token_match = self._TOKEN_PATTERN.search(resp)
        if not token_match:
            raise ValueError("Token not found in page HTML.")
        token_value = token_match.group(1)

        challenge_url = f"{url}?challenge={token_value}"
        _ = await self.fetch(challenge_url, **kwargs)
        return await self.fetch(url, **kwargs)
