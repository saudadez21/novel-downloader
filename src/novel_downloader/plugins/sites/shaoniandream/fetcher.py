#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.shaoniandream.fetcher
----------------------------------------------------
"""

import random
from typing import Any

from novel_downloader.plugins.base.fetcher import BaseSession
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import LoginField


@registrar.register_fetcher()
class ShaoniandreamSession(BaseSession):
    """
    A session class for interacting with the 少年梦 (www.shaoniandream.com) novel
    """

    site_name: str = "shaoniandream"

    BOOKCASE_URL = "https://www.shaoniandream.com/user/favobook"
    BOOK_INFO_URL = "https://www.shaoniandream.com/book_detail/{book_id}"
    BOOK_DETAIL_SIGN_UTL = "https://www.shaoniandream.com/booklibrary/getbookdetaildirsign/book_id/{book_id}"
    BOOK_DETAIL_URL = (
        "https://www.shaoniandream.com/booklibrary/getbookdetaildir/BookID/{book_id}"
    )
    CHAPTER_SIGN_URL = "https://www.shaoniandream.com/booklibrary/membersinglechaptersign/chapter_id/{chapter_id}"
    CHAPTER_URL = "https://www.shaoniandream.com/booklibrary/membersinglechapter/chapter_id/{chapter_id}"

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
        if not cookies:
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

        Order: [info, detail]

        :param book_id: The book identifier.
        :return: The page content as string list.
        """
        info_url = self.BOOK_INFO_URL.format(book_id=book_id)
        info_html = await self.fetch(info_url, **kwargs)

        detail_url = self.BOOK_DETAIL_URL.format(book_id=book_id)
        params = {"randomm": self._get_rand()}
        data = {
            "chapter_access_key": await self._get_book_detail_key(book_id),
        }
        async with self.post(detail_url, data=data, params=params) as resp:
            resp.raise_for_status()
            detail_html = await resp.text(encoding="utf-8")

        return [info_html, detail_html]

    async def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        url = self.CHAPTER_URL.format(chapter_id=chapter_id)
        params = {"randoom": self._get_rand()}
        data = {
            "chapter_access_key": await self._get_chapter_key(chapter_id),
            "isMarket": "1",
        }
        async with self.post(url, data=data, params=params) as resp:
            resp.raise_for_status()
            return [await resp.text(encoding="utf-8")]

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

    @staticmethod
    def _get_rand() -> str:
        return str(random.random())

    async def _get_book_detail_key(self, book_id: str) -> str:
        params = {"randoom": self._get_rand()}
        url = self.BOOK_DETAIL_SIGN_UTL.format(book_id=book_id)

        async with self.post(url, params=params) as resp:
            resp.raise_for_status()
            resp_json: dict[str, Any] = await resp.json(encoding="utf-8")

            if (
                resp_json.get("status") == 1
                and isinstance(resp_json.get("data"), dict)
                and "chapter_access_key" in resp_json["data"]
            ):
                return str(resp_json["data"]["chapter_access_key"])

            raise ValueError(f"Unexpected book detail response: {resp_json}")

    async def _get_chapter_key(self, chapter_id: str) -> str:
        params = {"randoom": self._get_rand()}
        url = self.CHAPTER_SIGN_URL.format(chapter_id=chapter_id)

        async with self.post(url, params=params) as resp:
            resp.raise_for_status()
            resp_json: dict[str, Any] = await resp.json(encoding="utf-8")

            if (
                resp_json.get("status") == 1
                and isinstance(resp_json.get("data"), dict)
                and "chapter_access_key" in resp_json["data"]
            ):
                return str(resp_json["data"]["chapter_access_key"])

            raise ValueError(f"Unexpected chapter key response: {resp_json}")

    async def _check_login_status(self) -> bool:
        """
        Check whether the user is currently logged in by
        inspecting the user home page api content.

        :return: True if the user is logged in, False otherwise.
        """
        try:
            bookcase_html = await self.fetch(self.BOOKCASE_URL)
            keywords = {"验证码登录", "账号密码登录"}
            return not any(kw in bookcase_html for kw in keywords)
        except Exception as e:
            self.logger.info("shaoniandream login check failed: %s", e)
        return False
