#!/usr/bin/env python3
"""
novel_downloader.core.requesters.esjzone.async_session
------------------------------------------------------

"""

import re
from typing import Any

from novel_downloader.config.models import RequesterConfig
from novel_downloader.core.requesters.base import BaseAsyncSession
from novel_downloader.utils.i18n import t
from novel_downloader.utils.state import state_mgr
from novel_downloader.utils.time_utils import async_sleep_with_random_delay


class EsjzoneAsyncSession(BaseAsyncSession):
    """
    A async session class for interacting with the
    esjzone (www.esjzone.cc) novel website.
    """

    BOOKCASE_URL = "https://www.esjzone.cc/my/favorite"
    BOOK_INFO_URL = "https://www.esjzone.cc/detail/{book_id}.html"
    CHAPTER_URL = "https://www.esjzone.cc/forum/{book_id}/{chapter_id}.html"

    API_LOGIN_URL_1 = "https://www.esjzone.cc/my/login"
    API_LOGIN_URL_2 = "https://www.esjzone.cc/inc/mem_login.php"

    def __init__(
        self,
        config: RequesterConfig,
    ):
        super().__init__(config)
        self._logged_in: bool = False
        self._request_interval = config.backoff_factor
        self._retry_times = config.retry_times
        self._username = config.username
        self._password = config.password

    async def login(
        self,
        username: str = "",
        password: str = "",
        manual_login: bool = False,
        **kwargs: Any,
    ) -> bool:
        """
        Restore cookies persisted by the session-based workflow.
        """
        cookies: dict[str, str] = state_mgr.get_cookies("esjzone")
        username = username or self._username
        password = password or self._password

        self.update_cookies(cookies)
        for _ in range(self._retry_times):
            if await self._check_login_status():
                self.logger.debug("[auth] Already logged in.")
                self._logged_in = True
                return True
            if username and password and not await self._api_login(username, password):
                print(t("session_login_failed", site="esjzone"))
            await async_sleep_with_random_delay(
                self._request_interval,
                mul_spread=1.1,
                max_sleep=self._request_interval + 2,
            )

        self._logged_in = await self._check_login_status()
        return self._logged_in

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
        page: int = 1,
        **kwargs: Any,
    ) -> list[str]:
        """
        Retrieve the user's *bookcase* page.

        :return: The HTML markup of the bookcase page.
        """
        url = self.bookcase_url()
        return [await self.fetch(url, **kwargs)]

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
            self.logger.warning("[session] _api_login failed at step 1: %s", exc)
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
            json_2 = await resp_2.json()
            resp_code: int = json_2.get("status", 301)
            return resp_code == 200
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
            "window.location.href='/my/login'",
        ]
        resp_text = await self.get_bookcase()
        if not resp_text:
            return False
        return not any(kw in resp_text[0] for kw in keywords)

    def _extract_token(self, text: str) -> str:
        match = re.search(r"<JinJing>(.+?)</JinJing>", text)
        return match.group(1) if match else ""

    async def _on_close(self) -> None:
        """
        Save cookies to the state manager before closing.
        """
        state_mgr.set_cookies("esjzone", self.cookies)
