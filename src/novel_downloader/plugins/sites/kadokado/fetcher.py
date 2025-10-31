#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.kadokado.fetcher
-----------------------------------------------
"""

import asyncio
from typing import Any

from novel_downloader.plugins.base.fetcher import BaseSession
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import LoginField


@registrar.register_fetcher()
class KadokadoSession(BaseSession):
    """
    A session class for interacting with the KadoKado (www.kadokado.com.tw) novel.
    """

    site_name: str = "kadokado"

    BOOK_INFO_URL = "https://api.kadokado.com.tw/v2/titles/{book_id}"
    BOOK_CATALOG_URL = "https://api.kadokado.com.tw/v3/title/{book_id}/collection"
    CHAPTER_INFO_URL = "https://api.kadokado.com.tw/v3/chapter/{chapter_id}/info"
    CHAPTER_CONT_URL = "https://api.kadokado.com.tw/v3/chapter/{chapter_id}/content"
    USER_API_URL = "https://api.kadokado.com.tw/v2/members/me"

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
        info_url = self.BOOK_INFO_URL.format(book_id=book_id)
        catalog_url = self.BOOK_CATALOG_URL.format(book_id=book_id)

        info_resp, catalog_resp = await asyncio.gather(
            self.fetch(info_url, **kwargs),
            self.fetch(catalog_url, **kwargs),
        )
        return [info_resp, catalog_resp]

    async def get_book_chapter(
        self,
        book_id: str,
        chapter_id: str,
        **kwargs: Any,
    ) -> list[str]:
        info_url = self.CHAPTER_INFO_URL.format(chapter_id=chapter_id)
        content_url = self.CHAPTER_CONT_URL.format(chapter_id=chapter_id)

        info_resp, content_resp = await asyncio.gather(
            self.fetch(info_url, **kwargs),
            self.fetch(content_url, **kwargs),
        )
        return [info_resp, content_resp]

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
        try:
            async with self.get(self.USER_API_URL) as resp:
                resp.raise_for_status()
                data = await resp.json()
                if isinstance(data, dict) and data.get("memberId"):
                    return True
                self.logger.debug("KadoKado login check response: %s", data)
                return False
        except Exception as e:
            self.logger.info("KadoKado login check failed: %s", e)
        return False
