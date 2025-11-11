#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n69hao.fetcher
---------------------------------------------
"""

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class N69haoFetcher(GenericFetcher):
    """
    A session class for interacting with the 69书吧 (www.69hao.com) novel.
    """

    site_name: str = "n69hao"

    BASE_URL = "https://www.69hao.com"
    BOOK_INFO_URL = "https://www.69hao.com/{book_id}/"

    USE_PAGINATED_CHAPTER = True

    @classmethod
    def relative_chapter_url(cls, book_id: str, chapter_id: str, idx: int) -> str:
        return (
            f"/{book_id}/{chapter_id}.html"
            if idx == 1
            else f"/{book_id}/{chapter_id}_{idx}.html"
        )
