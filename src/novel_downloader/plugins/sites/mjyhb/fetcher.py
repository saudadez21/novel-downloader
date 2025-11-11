#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.mjyhb.fetcher
--------------------------------------------
"""

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class MjyhbFetcher(GenericFetcher):
    """
    A session class for interacting with the 三五中文 (m.mjyhb.com) novel.
    """

    site_name: str = "mjyhb"

    BASE_URL = "https://m.mjyhb.com"
    BOOK_INFO_URL = "https://m.mjyhb.com/info_{book_id}/"

    USE_PAGINATED_CHAPTER = True

    @classmethod
    def relative_chapter_url(cls, book_id: str, chapter_id: str, idx: int) -> str:
        return (
            f"/read_{book_id}/{chapter_id}_{idx}.html"
            if idx > 1
            else f"/read_{book_id}/{chapter_id}.html"
        )
