#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.esjzone.fetcher
----------------------------------------------

"""

import re
from collections.abc import Mapping
from typing import Any

from novel_downloader.plugins.base.fetcher import BaseFetcher
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import LoginField


@registrar.register_fetcher()
class EsjzoneFetcher(BaseFetcher):
    """
    A session class for interacting with the ESJ Zone (www.esjzone.cc) novel.
    """

    site_name: str = "esjzone"

    BOOKCASE_URL = "https://www.esjzone.cc/my/favorite"
    BOOK_INFO_URL = "https://www.esjzone.cc/detail/{book_id}.html"
    CHAPTER_URL = "https://www.esjzone.cc/forum/{book_id}/{chapter_id}.html"

    _LOGIN_URL = "https://www.esjzone.cc/my/login"
    _API_LOGIN_URL = "https://www.esjzone.cc/inc/mem_login.php"
    _API_UNLOCK_URL = "https://www.esjzone.cc/inc/forum_pw.php"

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
            self.session.update_cookies(cookies)

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
        password: str | None = None,
        **kwargs: Any,
    ) -> list[str]:
        url = self.chapter_url(book_id=book_id, chapter_id=chapter_id)
        if password:
            await self._api_unlock_chapter(url, password)
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

    async def _get_auth_token(self, url: str) -> str:
        """
        Equivalent logic to the JavaScript `getAuthToken` function:
        retrieves an authentication token from the given URL for use
        in subsequent requests.

        The `url` is typically the page where the next request originates.

        Note:
            The site implements an older object-parameter-based callback
            mechanism in JavaScript.
        """
        data = {"plxf": "getAuthToken"}

        resp = await self.session.post(url, data=data)
        if not resp.ok:
            self.logger.warning(
                "esjzone getAuthToken HTTP failed for %s, status=%s", url, resp.status
            )
            return ""

        try:
            # Example response: <JinJing>token_here</JinJing>
            text = resp.text
            return self._extract_token(text)
        except Exception as exc:
            self.logger.warning(
                "esjzone getAuthToken parse failed for %s: %s", url, exc
            )
            return ""

    async def _api_login(self, username: str, password: str) -> bool:
        """
        Login to the API using a 2-step token-based process.

        Step 1: Get auth token.
        Step 2: Use token and credentials to perform login.

        :return: True if login succeeds, False otherwise.
        """
        token = await self._get_auth_token(self._LOGIN_URL)
        if not token:
            return False

        payload = {
            "email": username,
            "pwd": password,
            "remember_me": "on",
        }
        headers = {**self.headers, "Authorization": token}

        resp = await self.session.post(
            self._API_LOGIN_URL, data=payload, headers=headers
        )
        if not resp.ok:
            self.logger.warning("esjzone login HTTP failed, status=%s", resp.status)
            return False

        try:
            result = resp.json()
        except Exception as exc:
            self.logger.warning("esjzone login JSON parse failed: %s", exc)
            return False

        status_code: int = result.get("status", 301)
        if status_code != 200:
            self.logger.warning("esjzone login failed: %s", result.get("msg", ""))
            return False

        return True

    async def _api_unlock_chapter(self, chap_url: str, password: str) -> str:
        """
        Unlock a password-protected chapter.

        Step 1: Get auth token for the chapter page.
        Step 2: Use token + password to request the unlocked content.

        :param chap_url: The chapter page URL.
        :param password: The forum/chapter password provided by the user.
        :return: The unlocked chapter HTML if successful, else an empty string.
        """
        token = await self._get_auth_token(chap_url)
        if not token:
            return ""

        payload = {"pw": password}
        headers = {**self.headers, "Authorization": token}

        resp = await self.session.post(
            self._API_UNLOCK_URL, data=payload, headers=headers
        )
        if not resp.ok:
            self.logger.warning(
                "esjzone unlock HTTP failed for %s, status=%s", chap_url, resp.status
            )
            return ""

        try:
            result = resp.json()
        except Exception as exc:
            self.logger.warning(
                "esjzone unlock JSON parse failed for %s: %s", chap_url, exc
            )
            return ""

        if result.get("status") != 200:
            self.logger.warning(
                "esjzone unlock failed for %s: %s", chap_url, result.get("msg", "")
            )
            return ""

        return result.get("html") or ""

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
