#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.qidian.session
---------------------------------------------

"""

import base64
import hashlib
import json
import random
import time
from typing import Any, ClassVar

import aiohttp

from novel_downloader.core.fetchers.base import BaseSession
from novel_downloader.models import FetcherConfig, LoginField
from novel_downloader.utils.crypto_utils import rc4_crypt
from novel_downloader.utils.time_utils import async_sleep_with_random_delay


class QidianSession(BaseSession):
    """
    A session class for interacting with the Qidian (www.qidian.com) novel website.
    """

    HOMEPAGE_URL = "https://www.qidian.com/"
    BOOKCASE_URL = "https://my.qidian.com/bookcase/"
    # BOOK_INFO_URL = "https://book.qidian.com/info/{book_id}/"
    BOOK_INFO_URL = "https://www.qidian.com/book/{book_id}/"
    CHAPTER_URL = "https://www.qidian.com/chapter/{book_id}/{chapter_id}/"

    LOGIN_URL = "https://passport.qidian.com/"

    _cookie_keys: ClassVar[list[str]] = [
        "X2NzcmZUb2tlbg==",
        "eXdndWlk",
        "eXdvcGVuaWQ=",
        "eXdrZXk=",
        "d190c2Zw",
    ]

    def __init__(
        self,
        config: FetcherConfig,
        cookies: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__("qidian", config, cookies, **kwargs)
        self._fp_key = _d("ZmluZ2VycHJpbnQ=")
        self._ab_key = _d("YWJub3JtYWw=")
        self._ck_key = _d("Y2hlY2tzdW0=")
        self._lt_key = _d("bG9hZHRz")
        self._ts_key = _d("dGltZXN0YW1w")
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

    async def get_homepage(
        self,
        **kwargs: Any,
    ) -> list[str]:
        """
        Retrieve the site home page.

        :return: The HTML markup of the home page.
        """
        url = self.homepage_url()
        return [await self.fetch(url, **kwargs)]

    @property
    def login_fields(self) -> list[LoginField]:
        return [
            LoginField(
                name="cookies",
                label="Cookie",
                type="cookie",
                required=True,
                placeholder="请输入你的登录 Cookie",
                description="可以通过浏览器开发者工具复制已登录状态下的 Cookie",
            ),
        ]

    async def fetch(
        self,
        url: str,
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

        cookie_key = _d("d190c2Zw")

        for attempt in range(self.retry_times + 1):
            try:
                refreshed_token = self._build_payload_token(url)
                self.update_cookies({cookie_key: refreshed_token})

                async with self.session.get(url, **kwargs) as resp:
                    resp.raise_for_status()
                    text: str = await resp.text()
                    return text
            except aiohttp.ClientError:
                if attempt < self.retry_times:
                    await async_sleep_with_random_delay(
                        self.backoff_factor,
                        mul_spread=1.1,
                        max_sleep=self.backoff_factor + 2,
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

    @property
    def hostname(self) -> str:
        return "www.qidian.com"

    def _update_fp_val(
        self,
        *,
        key: str = "",
    ) -> None:
        """"""
        enc_token = self.get_cookie_value(_d("d190c2Zw"))
        if not enc_token:
            return
        if not key:
            key = _get_key()
        decrypted_json: str = rc4_crypt(key, enc_token, mode="decrypt")
        payload: dict[str, Any] = json.loads(decrypted_json)
        self._fp_val = payload.get(self._fp_key, "")
        self._ab_val = payload.get(self._ab_key, "0" * 32)

    def _build_payload_token(
        self,
        new_uri: str,
        *,
        key: str = "",
    ) -> str:
        """
        Patch a timestamp-bearing token with fresh timing and checksum info.

        :param new_uri: URI used in checksum generation.
        :type new_uri: str
        :param key: RC4 key extracted from front-end JavaScript (optional).
        :type key: str, optional

        :return: Updated token with new timing and checksum values.
        :rtype: str
        """
        if not self._fp_val or not self._ab_val:
            self._update_fp_val()
        if not key:
            key = _get_key()

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
        return rc4_crypt(
            key, json.dumps(new_payload, separators=(",", ":")), mode="encrypt"
        )

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

        Logs any missing keys as warnings.

        :param cookies: The cookie dictionary to validate.
        :return: True if all required keys are present, False otherwise.
        """
        required = {_d(k) for k in self._cookie_keys}
        actual = set(cookies)
        missing = required - actual
        if missing:
            self.logger.warning("Missing required cookies: %s", ", ".join(missing))
        return not missing


def _d(b: str) -> str:
    return base64.b64decode(b).decode()


def _get_key() -> str:
    encoded = "Lj1qYxMuaXBjMg=="
    decoded = base64.b64decode(encoded)
    key = "".join([chr(b ^ 0x5A) for b in decoded])
    return key
