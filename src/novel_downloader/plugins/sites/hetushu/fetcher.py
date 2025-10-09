#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.hetushu.fetcher
----------------------------------------------

"""

import asyncio
from typing import Any

from novel_downloader.plugins.base.fetcher import BaseSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class HetushuSession(BaseSession):
    """
    A session class for interacting with the 和图书 (www.hetushu.com) novel.
    """

    site_name: str = "hetushu"
    BASE_URL_MAP: dict[str, str] = {
        "simplified": "www.hetushu.com",
        "traditional": "www.hetubook.com",
    }
    DEFAULT_BASE_URL: str = "www.hetushu.com"

    BOOK_INFO_URL = "https://{base_url}/book/{book_id}/index.html"
    BOOK_CATALOG_URL = "https://{base_url}/book/{book_id}/dir.json"
    CHAPTER_URL = "https://{base_url}/book/{book_id}/{chapter_id}.html"
    CHAPTER_TOKEN_URL = "https://{base_url}/book/{book_id}/r{chapter_id}.json"

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
        info_url = self.BOOK_INFO_URL.format(base_url=self._base_url, book_id=book_id)
        catalog_url = self.BOOK_CATALOG_URL.format(
            base_url=self._base_url, book_id=book_id
        )

        info_html, catalog_html = await asyncio.gather(
            self.fetch(info_url, ssl=False, **kwargs),
            self.fetch(catalog_url, ssl=False, **kwargs),
        )
        return [info_html, catalog_html]

    async def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML of a single chapter asynchronously.

        Order: [content, token]

        :param book_id: The book identifier.
        :param chapter_id: The chapter identifier.
        :return: The page content as string list.
        """
        chapter_url = self.CHAPTER_URL.format(
            base_url=self._base_url, book_id=book_id, chapter_id=chapter_id
        )
        token_url = self.CHAPTER_TOKEN_URL.format(
            base_url=self._base_url, book_id=book_id, chapter_id=chapter_id
        )
        headers = {
            "Content-type": "application/x-www-form-urlencoded",
            "X-Requested-With": "XMLHttpRequest",
            "Referer": chapter_url,
        }
        chapter_html = await self.fetch(chapter_url, **kwargs)
        async with self.get(token_url, headers=headers, **kwargs) as token_resp:
            token = token_resp.headers.get("Token") or ""
        return [chapter_html, token]
