#!/usr/bin/env python3
"""
novel_downloader.core.requesters.qidian.session
-----------------------------------------------

This module defines the QidianRequester class for interacting with
the Qidian website.
It extends the BaseSession by adding methods for logging in and
retrieving book information.
"""

from __future__ import annotations

import base64
from http.cookies import SimpleCookie
from typing import Any, ClassVar

from requests import Response

from novel_downloader.config.models import RequesterConfig
from novel_downloader.core.requesters.base import BaseSession
from novel_downloader.utils.crypto_utils import patch_qd_payload_token
from novel_downloader.utils.i18n import t
from novel_downloader.utils.state import state_mgr


class QidianSession(BaseSession):
    """
    QidianRequester provides methods for interacting with Qidian.com,
    including checking login status and preparing book-related URLs.

    Inherits base session setup from BaseSession.
    """

    BOOKCASE_URL = "https://my.qidian.com/bookcase/"
    BOOK_INFO_URL = "https://book.qidian.com/info/{book_id}/"
    CHAPTER_URL = "https://www.qidian.com/chapter/{book_id}/{chapter_id}/"

    _cookie_keys: ClassVar[list[str]] = [
        "X2NzcmZUb2tlbg==",
        "eXdndWlk",
        "eXdvcGVuaWQ=",
        "eXdrZXk=",
        "d190c2Zw",
    ]

    def __init__(
        self,
        config: RequesterConfig,
    ):
        """
        Initialize the QidianSession with a session configuration.

        :param config: The RequesterConfig instance containing request settings.
        """
        super().__init__(config)
        self._logged_in: bool = False
        self._retry_times = config.retry_times
        self._retry_interval = config.backoff_factor
        self._timeout = config.timeout

    def login(
        self,
        username: str = "",
        password: str = "",
        manual_login: bool = False,
        **kwargs: Any,
    ) -> bool:
        """
        Restore cookies persisted by the session-based workflow.
        """
        cookies: dict[str, str] = state_mgr.get_cookies("qidian")

        # Merge cookies into both the internal cache and the live session
        self.update_cookies(cookies)
        for attempt in range(1, self._retry_times + 1):
            if self._check_login_status():
                self.logger.debug("[auth] Already logged in.")
                self._logged_in = True
                return True

            if attempt == 1:
                print(t("session_login_prompt_intro"))
            cookie_str = input(
                t(
                    "session_login_prompt_paste_cookie",
                    attempt=attempt,
                    max_retries=self._retry_times,
                )
            ).strip()

            cookies = self._parse_cookie_input(cookie_str)
            if not self._check_cookies(cookies):
                print(t("session_login_prompt_invalid_cookie"))
                continue

            self.update_cookies(cookies)
        return self._check_login_status()

    def get_book_info(
        self,
        book_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the raw HTML of the book info page.

        :param book_id: The book identifier.
        :return: The page content as a string.
        """
        url = self.book_info_url(book_id=book_id)
        try:
            resp = self.get(url, **kwargs)
            resp.raise_for_status()
            return [resp.text]
        except Exception as exc:
            self.logger.warning(
                "[session] get_book_info(%s) failed: %s",
                book_id,
                exc,
            )
        return []

    def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        """
        Fetch the HTML of a single chapter.

        :param book_id: The book identifier.
        :param chapter_id: The chapter identifier.
        :return: The chapter content as a string.
        """
        url = self.chapter_url(book_id=book_id, chapter_id=chapter_id)
        try:
            resp = self.get(url, **kwargs)
            resp.raise_for_status()
            return [resp.text]
        except Exception as exc:
            self.logger.warning(
                "[session] get_book_chapter(%s) failed: %s",
                book_id,
                exc,
            )
        return []

    def get_bookcase(
        self,
        page: int = 1,
        **kwargs: Any,
    ) -> list[str]:
        """
        Retrieve the user's *bookcase* page.

        :return: The HTML markup of the bookcase page.
        """
        url = self.bookcase_url()
        try:
            resp = self.get(url, **kwargs)
            resp.raise_for_status()
            return [resp.text]
        except Exception as exc:
            self.logger.warning(
                "[session] get_bookcase failed: %s",
                exc,
            )
        return []

    def get(
        self,
        url: str,
        params: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> Response:
        """
        Same as :py:meth:`BaseSession.get`, but transparently refreshes
        a cookie-based token used for request validation.

        The method:
        1. Reads the existing cookie (if any);
        2. Generates a new value tied to *url*;
        3. Updates both the live ``requests.Session`` and the internal cache;
        4. Delegates the actual request to ``super().get``.
        """
        if self._session is None:
            raise RuntimeError("Session is not initialized or has been shut down.")

        # ---- 1. refresh token cookie --------------------------------------
        cookie_key = self._d("d190c2Zw")
        old_token = self._session.cookies.get(cookie_key, "")

        if old_token:
            refreshed_token = patch_qd_payload_token(old_token, url)
            self._session.cookies.set(cookie_key, refreshed_token)
            self._cookies[cookie_key] = refreshed_token

        # ---- 2. perform the real GET --------------------------------------------
        resp: Response = super().get(url, params=params, **kwargs)

        # ---- 3. persist any server-set cookies (optional) --------------
        self.update_cookies(self._session.cookies.get_dict())
        state_mgr.set_cookies("qidian", self._cookies)

        return resp

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

    @classmethod
    def bookcase_url(cls) -> str:
        """
        Construct the URL for the user's bookcase page.

        :return: Fully qualified URL of the bookcase.
        """
        return cls.BOOKCASE_URL

    def _check_login_status(self) -> bool:
        """
        Check whether the user is currently logged in by
        inspecting the bookcase page content.

        :return: True if the user appears to be logged in, False otherwise.
        """
        keywords = [
            'var buid = "fffffffffffffffffff"',
            "C2WF946J0/probe.js",
        ]
        resp_text = self.get_bookcase()
        if not resp_text:
            return False
        return not any(kw in resp_text[0] for kw in keywords)

    @staticmethod
    def _parse_cookie_input(cookie_str: str) -> dict[str, str]:
        """
        Parse a raw cookie string (e.g. from browser dev tools) into a dict.
        Returns an empty dict if parsing fails.

        :param cookie_str: The raw cookie header string.
        :return: Parsed cookie dict.
        """
        filtered = "; ".join(pair for pair in cookie_str.split(";") if "=" in pair)
        parsed = SimpleCookie()
        try:
            parsed.load(filtered)
            return {k: v.value for k, v in parsed.items()}
        except Exception:
            return {}

    def _check_cookies(self, cookies: dict[str, str]) -> bool:
        """
        Check if the provided cookies contain all required keys.

        Logs any missing keys as warnings.

        :param cookies: The cookie dictionary to validate.
        :return: True if all required keys are present, False otherwise.
        """
        required = {self._d(k) for k in self._cookie_keys}
        actual = set(cookies)
        missing = required - actual
        if missing:
            self.logger.warning("Missing required cookies: %s", ", ".join(missing))
        return not missing

    @staticmethod
    def _d(b: str) -> str:
        return base64.b64decode(b).decode()
