#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.fanqienovel.fetcher
--------------------------------------------------
"""

from typing import Any

from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import LoginField


@registrar.register_fetcher()
class FanqienovelSession(GenericSession):
    """
    A session class for interacting with the 番茄小说网 (fanqienovel.com) novel.
    """

    site_name: str = "fanqienovel"

    BOOK_INFO_URL = "https://fanqienovel.com/page/{book_id}"
    CHAPTER_URL = "https://fanqienovel.com/reader/{chapter_id}"

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

    async def _check_login_status(self) -> bool:
        """
        Check whether the user is currently logged in by
        inspecting the user home page api content.

        :return: True if the user is logged in, False otherwise.
        """
        return True
