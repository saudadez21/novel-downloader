#!/usr/bin/env python3
"""
novel_downloader.plugins.archived.xiaoshuoge.fetcher
----------------------------------------------------

"""

import asyncio
from typing import Any

from novel_downloader.plugins.base.fetcher import BaseSession


class XiaoshuogeSession(BaseSession):
    """
    A session class for interacting with the 小说屋 (www.xiaoshuoge.info) novel.
    """

    site_name: str = "xiaoshuoge"

    BOOK_INFO_URL = "http://www.xiaoshuoge.info/book/{book_id}/"
    BOOK_CATALOG_URL = "http://www.xiaoshuoge.info/html/{book_id}/"
    CHAPTER_URL = "http://www.xiaoshuoge.info/html/{book_id}/{chapter_id}.html"

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
        book_id = book_id.replace("-", "/")
        url = self.chapter_url(book_id=book_id, chapter_id=chapter_id)
        return [await self.fetch(url, ssl=False, **kwargs)]

    @classmethod
    def book_info_url(cls, book_id: str) -> str:
        """
        Construct the URL for fetching a book's info page.

        :param book_id: The identifier of the book.
        :return: Fully qualified URL for the book info page.
        """
        clean_id = book_id.rsplit("/", 1)[-1]
        return cls.BOOK_INFO_URL.format(book_id=clean_id)

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
