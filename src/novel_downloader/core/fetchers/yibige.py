#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.yibige
-------------------------------------

"""

import asyncio
from typing import Any

from novel_downloader.core.fetchers.base import BaseSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["yibige"],
)
class YibigeSession(BaseSession):
    """
    A session class for interacting with the 一笔阁 (www.yibige.org) novel website.
    """

    site_name: str = "yibige"
    BASE_URL_MAP: dict[str, str] = {
        "simplified": "www.yibige.org",  # 主站
        "traditional": "tw.yibige.org",
        "singapore": "sg.yibige.org",  # 新加坡
        "taiwan": "tw.yibige.org",  # 臺灣正體
        "hongkong": "hk.yibige.org",  # 香港繁體
    }
    DEFAULT_BASE_URL: str = "www.yibige.org"

    BOOK_INFO_URL = "https://{base_url}/{book_id}/"
    BOOK_CATALOG_URL = "https://{base_url}/{book_id}/index.html"
    CHAPTER_URL = "https://{base_url}/{book_id}/{chapter_id}.html"

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
        info_url = self.book_info_url(base_url=self._base_url, book_id=book_id)
        catalog_url = self.book_catalog_url(base_url=self._base_url, book_id=book_id)

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
        url = self.chapter_url(
            base_url=self._base_url, book_id=book_id, chapter_id=chapter_id
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
