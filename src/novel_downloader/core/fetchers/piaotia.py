#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.piaotia
--------------------------------------

"""

import asyncio
from typing import Any

from novel_downloader.core.fetchers.base import BaseSession
from novel_downloader.core.fetchers.registry import register_fetcher
from novel_downloader.models import FetcherConfig


@register_fetcher(
    site_keys=["piaotia"],
)
class PiaotiaSession(BaseSession):
    """
    A session class for interacting with the 飘天文学网 (www.piaotia.com) novel website.
    """

    BOOK_INFO_URL = "https://www.piaotia.com/bookinfo/{book_id}.html"
    BOOK_CATALOG_URL = "https://www.piaotia.com/html/{book_id}/index.html"
    CHAPTER_URL = "https://www.piaotia.com/html/{book_id}/{chapter_id}.html"

    def __init__(
        self,
        config: FetcherConfig,
        cookies: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__("piaotia", config, cookies, **kwargs)

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
        book_id = book_id.replace("-", "/")
        info_url = self.book_info_url(book_id=book_id)
        catalog_url = self.book_catalog_url(book_id=book_id)

        info_html, catalog_html = await asyncio.gather(
            self.fetch(info_url, **kwargs),
            self.fetch(catalog_url, **kwargs),
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

        :param book_id: The book identifier.
        :param chapter_id: The chapter identifier.
        :return: The page content as string list.
        """
        book_id = book_id.replace("-", "/")
        url = self.chapter_url(book_id=book_id, chapter_id=chapter_id)
        return [await self.fetch(url, **kwargs)]

    @classmethod
    def book_info_url(cls, book_id: str) -> str:
        """
        Construct the URL for fetching a book's info page.

        :param book_id: The identifier of the book.
        :return: Fully qualified URL for the book info page.
        """
        return cls.BOOK_INFO_URL.format(book_id=book_id)

    @classmethod
    def book_catalog_url(cls, book_id: str) -> str:
        """
        Construct the URL for fetching a book's catalog page.

        :param book_id: The identifier of the book.
        :return: Fully qualified catalog page URL.
        """
        return cls.BOOK_CATALOG_URL.format(book_id=book_id)

    @classmethod
    def chapter_url(cls, book_id: str, chapter_id: str) -> str:
        """
        Construct the URL for fetching a specific chapter.

        :param book_id: The identifier of the book.
        :param chapter_id: The identifier of the chapter.
        :return: Fully qualified chapter URL.
        """
        return cls.CHAPTER_URL.format(book_id=book_id, chapter_id=chapter_id)
