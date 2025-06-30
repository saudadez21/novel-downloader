#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.yamibo.session
---------------------------------------------

"""

from typing import Any

from lxml import html

from novel_downloader.core.fetchers.base import BaseSession
from novel_downloader.models import FetcherConfig, LoginField
from novel_downloader.utils.time_utils import async_sleep_with_random_delay


class YamiboSession(BaseSession):
    """
    A session class for interacting with the Yamibo (www.yamibo.com) novel website.
    """

    BASE_URL = "https://www.yamibo.com"
    BOOKCASE_URL = "https://www.yamibo.com/my/fav"
    BOOK_INFO_URL = "https://www.yamibo.com/novel/{book_id}"
    CHAPTER_URL = "https://www.yamibo.com/novel/view-chapter?id={chapter_id}"

    LOGIN_URL = "https://www.yamibo.com/user/login"

    def __init__(
        self,
        config: FetcherConfig,
        cookies: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__("yamibo", config, cookies, **kwargs)

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
        if cookies:
            self.update_cookies(cookies)

        if await self._check_login_status():
            self._is_logged_in = True
            self.logger.debug("[auth] Logged in via cookies.")
            return True

        if not (username and password):
            self.logger.warning("[auth] No credentials provided.")
            return False

        for _ in range(attempt):
            if (
                await self._api_login(username, password)
                and await self._check_login_status()
            ):
                self._is_logged_in = True
                return True
            await async_sleep_with_random_delay(
                self.backoff_factor,
                mul_spread=1.1,
                max_sleep=self.backoff_factor + 2,
            )

        self._is_logged_in = False
        return False

    async def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML of the book info page asynchronously.

        :param book_id: The book identifier.
        :return: The page content as a string.
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

    @property
    def login_fields(self) -> list[LoginField]:
        return [
            LoginField(
                name="username",
                label="用户名",
                type="text",
                required=True,
                placeholder="请输入你的用户名",
                description="用于登录 www.yamibo.com 的用户名",
            ),
            LoginField(
                name="password",
                label="密码",
                type="password",
                required=True,
                placeholder="请输入你的密码",
                description="用于登录 www.yamibo.com 的密码",
            ),
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
    def chapter_url(cls, book_id: str, chapter_id: str) -> str:
        """
        Construct the URL for fetching a specific chapter.

        :param book_id: The identifier of the book.
        :param chapter_id: The identifier of the chapter.
        :return: Fully qualified chapter URL.
        """
        return cls.CHAPTER_URL.format(book_id=book_id, chapter_id=chapter_id)

    @property
    def hostname(self) -> str:
        return "www.yamibo.com"

    async def _api_login(self, username: str, password: str) -> bool:
        """
        Login to the API using a 2-step token-based process.

        Step 1: Get token `_csrf-frontend`.
        Step 2: Use token and credentials to perform login.
        Return True if login succeeds, False otherwise.
        """
        try:
            resp_1 = await self.get(self.LOGIN_URL)
            resp_1.raise_for_status()
            text_1 = await resp_1.text()
            tree = html.fromstring(text_1)
            csrf_value = tree.xpath('//input[@name="_csrf-frontend"]/@value')
            csrf_value = csrf_value[0] if csrf_value else ""
            if not csrf_value:
                self.logger.warning("[session] _api_login: CSRF token not found.")
                return False
        except Exception as exc:
            self.logger.warning("[session] _api_login failed at step 1: %s", exc)
            return False

        data_2 = {
            "_csrf-frontend": csrf_value,
            "LoginForm[username]": username,
            "LoginForm[password]": password,
            # "LoginForm[rememberMe]": 0,
            "LoginForm[rememberMe]": 1,
            "login-button": "",
        }
        temp_headers = dict(self.headers)
        temp_headers["Origin"] = self.BASE_URL
        temp_headers["Referer"] = self.LOGIN_URL
        try:
            resp_2 = await self.post(self.LOGIN_URL, data=data_2, headers=temp_headers)
            resp_2.raise_for_status()
            text_2 = await resp_2.text()
            return "登录成功" in text_2
        except Exception as exc:
            self.logger.warning("[session] _api_login failed at step 2: %s", exc)
        return False

    async def _check_login_status(self) -> bool:
        """
        Check whether the user is currently logged in by
        inspecting the bookcase page content.

        :return: True if the user is logged in, False otherwise.
        """
        keywords = [
            "登录 - 百合会",
            "用户名/邮箱",
        ]
        resp_text = await self.get_bookcase()
        if not resp_text:
            return False
        return not any(kw in resp_text[0] for kw in keywords)
