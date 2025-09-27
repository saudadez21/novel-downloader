#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.qidian.fetcher
---------------------------------------------

"""

import base64
import hashlib
import json
import random
import time
from collections.abc import Mapping
from typing import Any, ClassVar

import aiohttp

from novel_downloader.libs.crypto.rc4 import rc4_init, rc4_stream
from novel_downloader.libs.time_utils import async_jitter_sleep
from novel_downloader.plugins.base.fetcher import BaseSession
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import FetcherConfig, LoginField


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

    _cookie_keys: ClassVar[list[str]] = [
        "eXdndWlk",
        "d190c2Zw",
    ]

    def __init__(
        self,
        config: FetcherConfig,
        cookies: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(config, cookies, **kwargs)
        self._s_init = rc4_init(self._d2("dGcwOUl0Myo5aA=="))
        self._cookie_key = self._d("d190c2Zw")
        self._fp_key = self._d("ZmluZ2VycHJpbnQ=")
        self._ab_key = self._d("YWJub3JtYWw=")
        self._ck_key = self._d("Y2hlY2tzdW0=")
        self._lt_key = self._d("bG9hZHRz")
        self._ts_key = self._d("dGltZXN0YW1w")
        self._fp_val: str = ""
        self._ab_val: str = ""

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

    async def fetch(
        self,
        url: str,
        encoding: str | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Same as :py:meth:`BaseSession.fetch`, but transparently refreshes
        a cookie-based token used for request validation.

        The method:
          1. Reads the existing cookie (if any);
          2. Generates a new value tied to *url*;
          3. Updates the live ``requests.Session``;
        """
        if self._rate_limiter:
            await self._rate_limiter.wait()

        for attempt in range(self._retry_times + 1):
            try:
                refreshed_token = self._build_payload_token(url)
                self.update_cookies({self._cookie_key: refreshed_token})

                async with await self.get(url, **kwargs) as resp:
                    resp.raise_for_status()
                    text: str = await resp.text(encoding=encoding)
                    return text
            except aiohttp.ClientError:
                if attempt < self._retry_times:
                    await async_jitter_sleep(
                        self._backoff_factor,
                        mul_spread=1.1,
                        max_sleep=self._backoff_factor + 2,
                    )
                    continue
                raise

        raise RuntimeError("Unreachable code reached in fetch()")

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

    def _update_fp_val(self) -> None:
        """
        Decrypt the payload from cookie and update `_fp_val` and `_ab_val`.
        """
        enc_token = self._get_cookie_value(self._cookie_key)
        if not enc_token:
            return

        cipher_bytes = base64.b64decode(enc_token)
        plain_bytes = rc4_stream(self._s_init, cipher_bytes)
        decrypted_json = plain_bytes.decode("utf-8", errors="replace")
        payload: dict[str, Any] = json.loads(decrypted_json)
        self._fp_val = payload.get(self._fp_key, "")
        self._ab_val = payload.get(self._ab_key, "0" * 32)

    def _build_payload_token(self, new_uri: str) -> str:
        """
        Patch a timestamp-bearing token with fresh timing and checksum info.

        :param new_uri: URI used in checksum generation.
        :return: Updated token with new timing and checksum values.
        """
        if not self._fp_val or not self._ab_val:
            self._update_fp_val()

        # rebuild timing fields
        loadts = int(time.time() * 1000)  # ms since epoch
        # Simulate the JS duration: N(600, 150)  pushed into [300, 1000]
        duration = max(300, min(1000, int(random.normalvariate(600, 150))))
        timestamp = loadts + duration

        comb = f"{new_uri}{loadts}{self._fp_val}"
        ck_val = hashlib.md5(comb.encode("utf-8")).hexdigest()

        new_payload = {
            self._lt_key: loadts,
            self._ts_key: timestamp,
            self._fp_key: self._fp_val,
            self._ab_key: self._ab_val,
            self._ck_key: ck_val,
        }
        plain_bytes = json.dumps(new_payload, separators=(",", ":")).encode("utf-8")
        cipher_bytes = rc4_stream(self._s_init, plain_bytes)
        return base64.b64encode(cipher_bytes).decode("utf-8")

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
            self.logger.warning("Missing required cookies: %s", ", ".join(missing))
        return not missing

    def _get_cookie_value(self, key: str) -> str | None:
        for cookie in self.session.cookie_jar:
            if cookie.key == key:
                return str(cookie.value)
        return None

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

    @staticmethod
    def _d2(b: str) -> bytes:
        return base64.b64decode(b)
