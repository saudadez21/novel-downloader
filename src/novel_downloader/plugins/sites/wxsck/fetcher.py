#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.wxsck.fetcher
--------------------------------------------
"""

import logging
from typing import Any

from novel_downloader.plugins.base.fetcher import BaseFetcher
from novel_downloader.plugins.registry import registrar

logger = logging.getLogger(__name__)


@registrar.register_fetcher()
class WxsckFetcher(BaseFetcher):
    """
    A session class for interacting with the 万相书城 (wxsck.com) novel.
    """

    site_name: str = "wxsck"

    BASE_URL = "https://wxsck.com"
    BOOK_INFO_URL = "https://wxsck.com/book/{book_id}/"

    async def fetch_book_info(self, book_id: str, **kwargs: Any) -> list[str]:
        info_url = self.BOOK_INFO_URL.format(book_id=book_id)
        return [await self.fetch(info_url, allow_redirects=True, **kwargs)]

    async def fetch_chapter_content(
        self, book_id: str, chapter_id: str, **kwargs: Any
    ) -> list[str]:
        origin = self.BASE_URL
        pages: list[str] = []
        idx = 1
        suffix = self.relative_chapter_url(book_id, chapter_id, idx)

        while True:
            html = await self.fetch(origin + suffix, allow_redirects=True, **kwargs)
            pages.append(html)
            idx += 1
            suffix = self.relative_chapter_url(book_id, chapter_id, idx)
            if suffix not in html:
                break
            await self._sleep()

        return pages

    @classmethod
    def relative_chapter_url(cls, book_id: str, chapter_id: str, idx: int) -> str:
        return (
            f"/book/{book_id}/{chapter_id}_{idx}.html"
            if idx > 1
            else f"/book/{book_id}/{chapter_id}.html"
        )

    async def fetch_data(self, url: str, **kwargs: Any) -> bytes | None:
        kwargs.setdefault("allow_redirects", True)
        return await super().fetch_data(url, **kwargs)
