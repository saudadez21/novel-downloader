#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ruochu.fetcher
---------------------------------------------
"""

import time
from typing import Any

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class RuochuFetcher(GenericFetcher):
    """
    A session class for interacting with the 若初文学网 (www.ruochu.com) novel.
    """

    site_name: str = "ruochu"

    HAS_SEPARATE_CATALOG: bool = True
    BOOK_INFO_URL = "https://www.ruochu.com/book/{book_id}"
    BOOK_CATALOG_URL = "https://www.ruochu.com/chapter/{book_id}"
    CHAPTER_URL = "https://a.ruochu.com/ajax/chapter/content/{chapter_id}"

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
