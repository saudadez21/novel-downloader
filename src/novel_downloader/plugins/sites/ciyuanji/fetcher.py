#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ciyuanji.fetcher
-----------------------------------------------
"""

from typing import Any

from novel_downloader.plugins.base.fetcher import BaseSession
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import LoginField


@registrar.register_fetcher()
class CiyuanjiSession(BaseSession):
    """
    A session class for interacting with the 次元姬 (www.ciyuanji.com) novel.
    """

    site_name: str = "ciyuanji"

    BOOKCASE_URL = "https://www.ciyuanji.com/user/rack.html"
    BOOK_INFO_URL = "https://www.ciyuanji.com/b_d_{book_id}.html"
    CHAPTER_URL = "https://www.ciyuanji.com/chapter/{book_id}_{chapter_id}.html"

    async def login(
        self,
        username: str = "",
        password: str = "",
        cookies: dict[str, str] | None = None,
        attempt: int = 1,
        **kwargs: Any,
    ) -> bool:
        """
        Attempt to log in asynchronously.

        :returns: True if login succeeded.
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
        Fetch the raw HTML (or JSON) of the book info page asynchronously.

        :param book_id: The book identifier.
        :return: The page content as string list.
        """
        url = self.book_info_url(book_id=book_id)
        return [await self.fetch(url, **kwargs)]

    async def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML (or JSON) of a single chapter asynchronously.

        :param book_id: The book identifier.
        :param chapter_id: The chapter identifier.
        :return: The page content as string list.
        """
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

    async def _check_login_status(self) -> bool:
        """
        Check whether the user is currently logged in

        :return: True if the user is logged in, False otherwise.
        """
        keywords = [
            "其他登录方式",
            "注册&amp;登录",
        ]
        resp_text = await self.get_bookcase()
        if not resp_text:
            return False
        return not any(kw in resp_text[0] for kw in keywords)

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
    def chapter_url(cls, book_id: str, chapter_id: str) -> str:
        """
        Construct the URL for fetching a specific chapter.

        :param book_id: The identifier of the book.
        :param chapter_id: The identifier of the chapter.
        :return: Fully qualified chapter URL.
        """
        return cls.CHAPTER_URL.format(book_id=book_id, chapter_id=chapter_id)
