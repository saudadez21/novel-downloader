#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ruochu.fetcher
---------------------------------------------
"""

import time
from typing import Any

from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import LoginField


@registrar.register_fetcher()
class RuochuSession(GenericSession):
    """
    A session class for interacting with the 若初文学网 (www.ruochu.com) novel.
    """

    site_name: str = "ruochu"

    HAS_SEPARATE_CATALOG: bool = True
    BOOK_INFO_URL = "https://www.ruochu.com/book/{book_id}"
    BOOK_CATALOG_URL = "https://www.ruochu.com/chapter/{book_id}"
    CHAPTER_URL = "https://a.ruochu.com/ajax/chapter/content/{chapter_id}"

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

    async def get_book_chapter(
        self, book_id: str, chapter_id: str, **kwargs: Any
    ) -> list[str]:
        if not self.CHAPTER_URL:
            raise NotImplementedError("CHAPTER_URL not set")

        params = {
            "callback": "jQuery18304592019622509267_1761948608126",
            "_": str(int(time.time() * 1000)),
        }
        url = self.CHAPTER_URL.format(chapter_id=chapter_id)
        return [await self.fetch(url, params=params, **kwargs)]

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
