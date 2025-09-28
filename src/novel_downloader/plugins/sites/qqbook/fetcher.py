#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.qqbook.fetcher
---------------------------------------------

"""

import asyncio
from typing import Any

from novel_downloader.plugins.base.fetcher import BaseSession
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import LoginField


@registrar.register_fetcher()
class QqbookSession(BaseSession):
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

    async def login(
        self,
        username: str = "",
        password: str = "",
        cookies: dict[str, str] | None = None,
        attempt: int = 1,
        **kwargs: Any,
    ) -> bool:
        """
        Restore cookies persisted by the session-based workflow.
        """
        if not cookies:
            return False
        self.update_cookies(cookies)

        self._is_logged_in = await self._check_login_status()
        return self._is_logged_in

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
        url = self.bookcase_url()
        return [await self.fetch(url, **kwargs)]

    @property
    def login_fields(self) -> list[LoginField]:
        return [
            LoginField(
                name="cookies",
                label="Cookie",
                type="cookie",
                required=True,
                placeholder="Paste your login cookies here",
                description="Copy the cookies from your browser's developer tools while logged in.",  # noqa: E501
            ),
        ]

    @classmethod
    def homepage_url(cls) -> str:
        """
        Construct the URL for the site home page.

        :return: Fully qualified URL of the home page.
        """
        return cls.HOMEPAGE_URL

    @classmethod
    def bookcase_url(cls) -> str:
        """
        Construct the URL for the user's bookcase page.

        :return: Fully qualified URL of the bookcase.
        """
        return cls.BOOKCASE_URL

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
            resp = await self.get(self.USER_HOMEPAGE_API_URL)
            resp.raise_for_status()
            payload = await resp.json(encoding="utf-8")
            if payload.get("code") == 0:
                return True
            self.logger.info(
                "QQ book login invalid (code=%s): %s",
                payload.get("code"),
                payload.get("msg"),
            )
        except Exception as e:
            self.logger.info("QQ book login check failed: %s", e)
        return False
