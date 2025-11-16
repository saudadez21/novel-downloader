#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.yodu.fetcher
-------------------------------------------

"""

import logging
from typing import Any

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar

logger = logging.getLogger(__name__)


@registrar.register_fetcher()
class YoduFetcher(GenericFetcher):
    """
    A session class for interacting with the 有度中文网 (www.yodu.org) novel.
    """

    site_name: str = "yodu"

    BASE_URL = "https://www.yodu.org"
    BOOK_INFO_URL = "https://www.yodu.org/book/{book_id}/"

    USE_PAGINATED_CHAPTER = True

    @classmethod
    def relative_chapter_url(cls, book_id: str, chapter_id: str, idx: int) -> str:
        return (
            f"/book/{book_id}/{chapter_id}_{idx}.html"
            if idx > 1
            else f"/book/{book_id}/{chapter_id}.html"
        )

    async def fetch_data(self, url: str, **kwargs: Any) -> bytes | None:
        kwargs.setdefault("verify", True)
        return await super().fetch_data(url, **kwargs)
