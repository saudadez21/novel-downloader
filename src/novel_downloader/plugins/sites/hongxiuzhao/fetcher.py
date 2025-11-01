#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.hongxiuzhao.fetcher
--------------------------------------------------
"""

from typing import Any

from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import LoginField


@registrar.register_fetcher()
class HongxiuzhaoSession(GenericSession):
    """
    A session class for interacting with the 红袖招 (hongxiuzhao.net) novel
    """

    site_name: str = "hongxiuzhao"

    BASE_URL = "https://hongxiuzhao.net"
    BOOK_INFO_URL = "https://hongxiuzhao.net/{book_id}.html"
    BOOKCASE_URL = "https://www.ciyuanji.com/user/rack.html"

    USE_PAGINATED_CHAPTER = True

    async def login(
        self,
        username: str = "",
        password: str = "",
        cookies: dict[str, str] | None = None,
        attempt: int = 1,
        **kwargs: Any,
    ) -> bool:
        """
        Attempt to log in asynchronously.

        :returns: True if login succeeded.
        """
        if not cookies:
            return False
        self.update_cookies(cookies)

        self._is_logged_in = await self._check_login_status()
        return self._is_logged_in

    @classmethod
    def relative_chapter_url(cls, book_id: str, chapter_id: str, idx: int) -> str:
        return f"/{chapter_id}.html" if idx == 1 else f"/{chapter_id}_{idx}.html"

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

    async def _check_login_status(self) -> bool:
        """
        Check whether the user is currently logged in

        :return: True if the user is logged in, False otherwise.
        """
        keywords = [
            # "请输入账号",
            # "请输入密码",
            "Enable JavaScript and cookies to continue",
        ]
        resp_text = await self.get_bookcase()
        if not resp_text:
            return False
        return not any(kw in resp_text[0] for kw in keywords)

    @classmethod
    def bookcase_url(cls) -> str:
        """
        Construct the URL for the user's bookcase page.

        :return: Fully qualified URL of the bookcase.
        """
        return cls.BOOKCASE_URL
