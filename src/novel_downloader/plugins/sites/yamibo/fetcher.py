#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.yamibo.fetcher
---------------------------------------------

"""

from collections.abc import Mapping
from typing import Any

from lxml import html
from novel_downloader.plugins.base.fetcher import BaseFetcher
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import LoginField


@registrar.register_fetcher()
class YamiboFetcher(BaseFetcher):
    """
    A session class for interacting with the 百合会 (www.yamibo.com) novel.
    """

    site_name: str = "yamibo"

    BASE_URL = "https://www.yamibo.com"
    BOOKCASE_URL = "https://www.yamibo.com/my/fav"
    BOOK_INFO_URL = "https://www.yamibo.com/novel/{book_id}"
    CHAPTER_URL = "https://www.yamibo.com/novel/view-chapter?id={chapter_id}"

    LOGIN_URL = "https://www.yamibo.com/user/login"

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
            self.session.update_cookies(cookies)

        if await self._check_login_status():
            self._is_logged_in = True
            self.logger.debug("Logged in via cookies: yamibo")
            return True

        if not (username and password):
            self.logger.warning("No credentials provided: yamibo")
            return False

        for _ in range(attempt):
            if (
                await self._api_login(username, password)
                and await self._check_login_status()
            ):
                self._is_logged_in = True
                return True
            await self._sleep()

        self._is_logged_in = False
        return False

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
        return [await self.fetch(self.BOOKCASE_URL, **kwargs)]

    @property
    def login_fields(self) -> list[LoginField]:
        return [
            LoginField(
                name="username",
                label="Username",
                type="text",
                required=True,
                placeholder="Enter your username",
                description="The username used for login",
            ),
            LoginField(
                name="password",
                label="Password",
                type="password",
                required=True,
                placeholder="Enter your password",
                description="The password used for login",
            ),
        ]

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

    async def _api_login(self, username: str, password: str) -> bool:
        """
        Login to the API using a 2-step token-based process.

        Step 1: Get token `_csrf-frontend`.
        Step 2: Use token and credentials to perform login.
        Return True if login succeeds, False otherwise.
        """
        try:
            resp_1 = await self.session.get(self.LOGIN_URL)
        except Exception as exc:
            self.logger.warning("yamibo _api_login failed at step 1 (request): %s", exc)
            return False

        if not resp_1.ok:
            self.logger.warning(
                "yamibo _api_login HTTP error at step 1: %s, status=%s",
                self.LOGIN_URL,
                resp_1.status,
            )
            return False

        try:
            tree = html.fromstring(resp_1.text)
            csrf_value_list = tree.xpath('//input[@name="_csrf-frontend"]/@value')
            csrf_value = csrf_value_list[0] if csrf_value_list else ""
        except Exception as exc:
            self.logger.warning("yamibo _api_login parse error at step 1: %s", exc)
            return False

        if not csrf_value:
            self.logger.warning("yamibo _api_login: CSRF token not found.")
            return False

        data_2 = {
            "_csrf-frontend": csrf_value,
            "LoginForm[username]": username,
            "LoginForm[password]": password,
            # "LoginForm[rememberMe]": 0,
            "LoginForm[rememberMe]": 1,
            "login-button": "",
        }
        headers = {
            **self.headers,
            "Origin": self.BASE_URL,
            "Referer": self.LOGIN_URL,
        }

        try:
            resp_2 = await self.session.post(
                self.LOGIN_URL, data=data_2, headers=headers
            )
        except Exception as exc:
            self.logger.warning("yamibo _api_login failed at step 2 (request): %s", exc)
            return False

        if not resp_2.ok:
            self.logger.warning(
                "yamibo _api_login HTTP error at step 2: %s, status=%s",
                self.LOGIN_URL,
                resp_2.status,
            )
            return False

        text_2 = resp_2.text
        return "登录成功" in text_2

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

    @staticmethod
    def _filter_cookies(
        raw_cookies: list[Mapping[str, Any]],
    ) -> dict[str, str]:
        ALLOWED_DOMAINS = {"www.yamibo.com", "bbs.yamibo.com", ""}
        return {
            c["name"]: c["value"]
            for c in raw_cookies
            if c.get("domain", "") in ALLOWED_DOMAINS
        }
