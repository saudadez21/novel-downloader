#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.kadokado.fetcher
-----------------------------------------------
"""

import asyncio
from typing import Any

from novel_downloader.plugins.base.fetcher import BaseFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class KadokadoFetcher(BaseFetcher):
    """
    A session class for interacting with the KadoKado (www.kadokado.com.tw) novel.
    """

    site_name: str = "kadokado"

    BOOK_INFO_URL = "https://api.kadokado.com.tw/v2/titles/{book_id}"
    BOOK_CATALOG_URL = "https://api.kadokado.com.tw/v3/title/{book_id}/collection"
    CHAPTER_INFO_URL = "https://api.kadokado.com.tw/v3/chapter/{chapter_id}/info"
    CHAPTER_CONT_URL = "https://api.kadokado.com.tw/v3/chapter/{chapter_id}/content"
    USER_API_URL = "https://api.kadokado.com.tw/v2/members/me"

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

    async def _check_login_status(self) -> bool:
        """
        Check whether the user is currently logged in by
        querying the KadoKado user info API.
        """
        try:
            resp = await self.session.get(self.USER_API_URL)
        except Exception as e:
            self.logger.info("KadoKado login check request failed: %s", e)
            return False

        if not resp.ok:
            self.logger.info("KadoKado login check HTTP failed: status=%s", resp.status)
            return False

        try:
            data = resp.json()
        except Exception as e:
            self.logger.info("KadoKado login check JSON parse failed: %s", e)
            return False

        if isinstance(data, dict) and data.get("memberId"):
            return True

        self.logger.debug("KadoKado login check response: %s", data)
        return False
