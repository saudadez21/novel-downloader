#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.qqbook.fetcher
---------------------------------------------

"""

import asyncio
from typing import Any

from novel_downloader.plugins.base.fetcher import BaseFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class QqbookFetcher(BaseFetcher):
    """
    A session class for interacting with the QQ 阅读 (book.qq.com) novel.
    """

    site_name: str = "qqbook"

    HOMEPAGE_URL = "https://book.qq.com/"
    BOOKCASE_URL = "https://book.qq.com/book-shelf"
    BOOK_INFO_URL = "https://book.qq.com/book-detail/{book_id}"
    BOOK_CATALOG_URL = "https://book.qq.com/api/book/detail/chapters?bid={book_id}"
    CHAPTER_URL = "https://book.qq.com/book-read/{book_id}/{chapter_id}/"

    USER_HOMEPAGE_API_URL = "https://book.qq.com/api/user/homepage"

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
        url = self.chapter_url(book_id=book_id, chapter_id=chapter_id)
        return [await self.fetch(url, **kwargs)]

    async def get_bookcase(
        self,
        **kwargs: Any,
    ) -> list[str]:
        """
        Retrieve the user's *bookcase* page.

        :return: The HTML markup of the bookcase page.
        """
        return [await self.fetch(self.BOOKCASE_URL, **kwargs)]

    @classmethod
    def homepage_url(cls) -> str:
        """
        Construct the URL for the site home page.

        :return: Fully qualified URL of the home page.
        """
        return cls.HOMEPAGE_URL

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

    async def _check_login_status(self) -> bool:
        """
        Check whether the user is currently logged in by
        inspecting the user home page api content.

        :return: True if the user is logged in, False otherwise.
        """
        try:
            resp = await self.session.get(self.USER_HOMEPAGE_API_URL)
        except Exception as e:
            self.logger.info("QQ book login check request failed: %s", e)
            return False

        if not resp.ok:
            self.logger.info("QQ book login check HTTP failed: status=%s", resp.status)
            return False

        try:
            payload = resp.json()
        except Exception as e:
            self.logger.info("QQ book login check JSON parse failed: %s", e)
            return False

        if payload.get("code") == 0:
            return True

        self.logger.info(
            "QQ book login invalid (code=%s): %s",
            payload.get("code"),
            payload.get("msg"),
        )
        return False
