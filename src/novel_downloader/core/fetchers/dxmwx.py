#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.dxmwx
------------------------------------

"""

import asyncio
from typing import Any

from novel_downloader.core.fetchers.base import BaseSession
from novel_downloader.core.fetchers.registry import register_fetcher
from novel_downloader.models import FetcherConfig


@register_fetcher(
    site_keys=["dxmwx"],
)
class DxmwxSession(BaseSession):
    """
    A session class for interacting with the 大熊猫文学网 (www.dxmwx.org) novel website.
    """

    BOOK_INFO_URL = "https://{base_url}/book/{book_id}.html"
    BOOK_CATALOG_URL = "https://{base_url}/chapter/{book_id}.html"
    CHAPTER_URL = "https://{base_url}/read/{book_id}_{chapter_id}.html"

    def __init__(
        self,
        config: FetcherConfig,
        cookies: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__("dxmwx", config, cookies, **kwargs)
        self.base_url = (
            "www.dxmwx.org" if config.locale_style == "simplified" else "tw.dxmwx.org"
        )

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
        info_url = self.book_info_url(base_url=self.base_url, book_id=book_id)
        catalog_url = self.book_catalog_url(base_url=self.base_url, book_id=book_id)

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
        url = self.chapter_url(
            base_url=self.base_url, book_id=book_id, chapter_id=chapter_id
        )
        return [await self.fetch(url, **kwargs)]

    @classmethod
    def book_info_url(cls, base_url: str, book_id: str) -> str:
        """
        Construct the URL for fetching a book's info page.

        :param book_id: The identifier of the book.
        :return: Fully qualified URL for the book info page.
        """
        return cls.BOOK_INFO_URL.format(base_url=base_url, book_id=book_id)

    @classmethod
    def book_catalog_url(cls, base_url: str, book_id: str) -> str:
        """
        Construct the URL for fetching a book's catalog page.

        :param book_id: The identifier of the book.
        :return: Fully qualified catalog page URL.
        """
        return cls.BOOK_CATALOG_URL.format(base_url=base_url, book_id=book_id)

    @classmethod
    def chapter_url(cls, base_url: str, book_id: str, chapter_id: str) -> str:
        """
        Construct the URL for fetching a specific chapter.

        :param book_id: The identifier of the book.
        :param chapter_id: The identifier of the chapter.
        :return: Fully qualified chapter URL.
        """
        return cls.CHAPTER_URL.format(
            base_url=base_url, book_id=book_id, chapter_id=chapter_id
        )
