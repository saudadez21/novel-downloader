#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.sfacg.browser
--------------------------------------------

"""

from typing import Any

from novel_downloader.core.fetchers.base import BaseBrowser
from novel_downloader.models import FetcherConfig, LoginField
from novel_downloader.utils.i18n import t


class SfacgBrowser(BaseBrowser):
    """
    A browser class for interacting with the Sfacg (m.sfacg.com) novel website.
    """

    LOGIN_URL = "https://m.sfacg.com/login"
    BOOKCASE_URL = "https://m.sfacg.com/sheets/"
    BOOK_INFO_URL = "https://m.sfacg.com/b/{book_id}/"
    BOOK_CATALOG_URL = "https://m.sfacg.com/i/{book_id}/"
    CHAPTER_URL = "https://m.sfacg.com/c/{chapter_id}/"

    def __init__(
        self,
        config: FetcherConfig,
        reuse_page: bool = False,
        **kwargs: Any,
    ) -> None:
        super().__init__("sfacg", config, reuse_page, **kwargs)

    async def login(
        self,
        username: str = "",
        password: str = "",
        cookies: dict[str, str] | None = None,
        attempt: int = 1,
        **kwargs: Any,
    ) -> bool:
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
        :return: The page content as a string.
        """
        info_url = self.book_info_url(book_id=book_id)
        catalog_url = self.book_catalog_url(book_id=book_id)

        info_html = await self.fetch(info_url, **kwargs)
        catalog_html = await self.fetch(catalog_url, **kwargs)

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
        :return: The chapter content as a string.
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

    async def set_interactive_mode(self, enable: bool) -> bool:
        """
        Enable or disable interactive mode for manual login.

        :param enable: True to enable, False to disable interactive mode.
        :return: True if operation or login check succeeded, False otherwise.
        """
        if enable:
            if self.headless:
                await self._restart_browser(headless=False)
            if self._manual_page is None:
                self._manual_page = await self.context.new_page()
            await self._manual_page.goto(self.LOGIN_URL)
            return True

        # restore
        if self._manual_page:
            await self._manual_page.close()
        self._manual_page = None
        if self.headless:
            await self._restart_browser(headless=True)
            self._is_logged_in = await self._check_login_status()
        return self.is_logged_in

    @property
    def login_fields(self) -> list[LoginField]:
        return [
            LoginField(
                name="manual_login",
                label="手动登录",
                type="manual_login",
                required=True,
                description=t("login_prompt_intro"),
            )
        ]

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
        return cls.CHAPTER_URL.format(chapter_id=chapter_id)

    @property
    def hostname(self) -> str:
        return "m.sfacg.com"

    async def _check_login_status(self) -> bool:
        """
        Check whether the user is currently logged in by
        inspecting the bookcase page content.

        :return: True if the user is logged in, False otherwise.
        """
        keywords = [
            "请输入用户名和密码",
            "用户未登录",
            "可输入用户名",
        ]
        resp_text = await self.get_bookcase()
        if not resp_text:
            return False
        return not any(kw in resp_text[0] for kw in keywords)
