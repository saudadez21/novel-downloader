#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.esjzone
--------------------------------------

"""

import re
from collections.abc import Mapping
from typing import Any

from novel_downloader.core.fetchers.base import BaseSession
from novel_downloader.core.fetchers.registry import register_fetcher
from novel_downloader.models import LoginField


@register_fetcher(
    site_keys=["esjzone"],
)
class EsjzoneSession(BaseSession):
    """
    A session class for interacting with the ESJ Zone (www.esjzone.cc) novel.
    """

    site_name: str = "esjzone"

    BOOKCASE_URL = "https://www.esjzone.cc/my/favorite"
    BOOK_INFO_URL = "https://www.esjzone.cc/detail/{book_id}.html"
    CHAPTER_URL = "https://www.esjzone.cc/forum/{book_id}/{chapter_id}.html"

    API_LOGIN_URL_1 = "https://www.esjzone.cc/my/login"
    API_LOGIN_URL_2 = "https://www.esjzone.cc/inc/mem_login.php"

    _TOKEN_RE = re.compile(r"<JinJing>(.*?)</JinJing>")

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
            self.logger.debug("Logged in via cookies: esjzone")
            return True

        if not (username and password):
            self.logger.warning("No credentials provided: esjzone")
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
                description="用于登录 esjzone.cc 的用户名",
            ),
            LoginField(
                name="password",
                label="密码",
                type="password",
                required=True,
                placeholder="请输入你的密码",
                description="用于登录 esjzone.cc 的密码",
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

    async def _api_login(self, username: str, password: str) -> bool:
        """
        Login to the API using a 2-step token-based process.

        Step 1: Get auth token.
        Step 2: Use token and credentials to perform login.
        Return True if login succeeds, False otherwise.
        """
        data_1 = {
            "plxf": "getAuthToken",
        }
        try:
            resp_1 = await self.post(self.API_LOGIN_URL_1, data=data_1)
            resp_1.raise_for_status()
            # Example response: <JinJing>token_here</JinJing>
            text_1 = await resp_1.text()
            token = self._extract_token(text_1)
        except Exception as exc:
            self.logger.warning("esjzone _api_login failed at step 1: %s", exc)
            return False

        data_2 = {
            "email": username,
            "pwd": password,
            "remember_me": "on",
        }
        temp_headers = dict(self.headers)
        temp_headers["Authorization"] = token
        try:
            resp_2 = await self.post(
                self.API_LOGIN_URL_2, data=data_2, headers=temp_headers
            )
            resp_2.raise_for_status()
            json_2 = await resp_2.json(content_type="text/html", encoding="utf-8")
            resp_code: int = json_2.get("status", 301)
            return resp_code == 200
        except Exception as exc:
            self.logger.warning("esjzone _api_login failed at step 2: %s", exc)
        return False

    async def _check_login_status(self) -> bool:
        """
        Check whether the user is currently logged in by
        inspecting the bookcase page content.

        :return: True if the user is logged in, False otherwise.
        """
        keywords = [
            "window.location.href='/my/login'",
            "會員登入",
            "會員註冊 SIGN UP",
        ]
        resp_text = await self.get_bookcase()
        if not resp_text:
            return False
        return not any(kw in resp_text[0] for kw in keywords)

    def _extract_token(self, text: str) -> str:
        return m.group(1) if (m := self._TOKEN_RE.search(text)) else ""

    @staticmethod
    def _filter_cookies(
        raw_cookies: list[Mapping[str, Any]],
    ) -> dict[str, str]:
        ALLOWED_DOMAINS = {".www.esjzone.cc", "www.esjzone.cc", ".esjzone.cc", ""}
        return {
            c["name"]: c["value"]
            for c in raw_cookies
            if c.get("domain", "") in ALLOWED_DOMAINS
        }
