#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.qidian.fetcher
---------------------------------------------

"""

import base64
from collections.abc import Mapping
from typing import Any, ClassVar

from novel_downloader.plugins.base.fetcher import BaseSession
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import LoginField


@registrar.register_fetcher()
class QidianSession(BaseSession):
    """
    A session class for interacting with the 起点中文网 (www.qidian.com) novel.
    """

    site_name: str = "qidian"

    HOMEPAGE_URL = "https://www.qidian.com/"
    BOOKCASE_URL = "https://my.qidian.com/bookcase/"
    BOOK_INFO_URL = "https://www.qidian.com/book/{book_id}/"
    CHAPTER_URL = "https://www.qidian.com/chapter/{book_id}/{chapter_id}/"

    LOGIN_URL = "https://passport.qidian.com/"

    _cookie_keys: ClassVar[list[str]] = ["eXdndWlk"]

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
        if not cookies or not self._check_cookies(cookies):
            return False
        self.update_cookies(cookies)

        self._is_logged_in = await self._check_login_status()
        return self._is_logged_in

    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        url = self.book_info_url(book_id=book_id)
        return [await self.fetch(url, **kwargs)]

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
        inspecting the bookcase page content.

        :return: True if the user is logged in, False otherwise.
        """
        keywords = [
            'var buid = "fffffffffffffffffff"',
            "C2WF946J0/probe.js",
            "login-area-wrap",
        ]
        resp_text = await self.get_bookcase()
        if not resp_text:
            return False
        return not any(kw in resp_text[0] for kw in keywords)

    def _check_cookies(self, cookies: dict[str, str]) -> bool:
        """
        Check if the provided cookies contain all required keys.

        :param cookies: The cookie dictionary to validate.
        :return: True if all required keys are present, False otherwise.
        """
        required = {self._d(k) for k in self._cookie_keys}
        actual = set(cookies)
        missing = required - actual
        if missing:
            self.logger.warning(
                "Missing required cookies (qidian): %s", ", ".join(missing)
            )
        return not missing

    @staticmethod
    def _filter_cookies(
        raw_cookies: list[Mapping[str, Any]],
    ) -> dict[str, str]:
        ALLOWED_DOMAINS = {".qidian.com", "www.qidian.com", ""}
        return {
            c["name"]: c["value"]
            for c in raw_cookies
            if c.get("domain", "") in ALLOWED_DOMAINS
        }

    @staticmethod
    def _d(b: str) -> str:
        return base64.b64decode(b).decode()
