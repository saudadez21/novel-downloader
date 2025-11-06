#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.wxsck.fetcher
--------------------------------------------
"""

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class WxsckFetcher(GenericFetcher):
    """
    A session class for interacting with the 万相书城 (wxsck.com) novel.
    """

    site_name: str = "wxsck"

    BASE_URL = "https://wxsck.com"
    BOOK_INFO_URL = "https://wxsck.com/book/{book_id}/"

    USE_PAGINATED_CHAPTER = True

    @classmethod
    def relative_chapter_url(cls, book_id: str, chapter_id: str, idx: int) -> str:
        return (
            f"/book/{book_id}/{chapter_id}_{idx}.html"
            if idx > 1
            else f"/book/{book_id}/{chapter_id}.html"
        )
