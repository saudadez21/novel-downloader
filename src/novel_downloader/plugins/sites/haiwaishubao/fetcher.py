#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.haiwaishubao.fetcher
---------------------------------------------------
"""

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class HaiwaishubaoFetcher(GenericFetcher):
    """
    A session class for interacting with the 海外书包 (www.haiwaishubao.com) novel
    """

    site_name: str = "haiwaishubao"

    HAS_SEPARATE_CATALOG = True
    BASE_URL = "https://www.haiwaishubao.com"
    BOOK_INFO_URL = "https://www.haiwaishubao.com/book/{book_id}/"
    BOOK_CATALOG_URL = "https://www.haiwaishubao.com/index/{book_id}/"
    CHAPTER_URL = "https://www.haiwaishubao.com/book/{book_id}/{chapter_id}.html"

    USE_PAGINATED_CATALOG = True
    USE_PAGINATED_CHAPTER = True

    @classmethod
    def relative_catalog_url(cls, book_id: str, idx: int) -> str:
        return f"/index/{book_id}/" if idx == 1 else f"/index/{book_id}/{idx}/"

    @classmethod
    def relative_chapter_url(cls, book_id: str, chapter_id: str, idx: int) -> str:
        return (
            f"/book/{book_id}/{chapter_id}.html"
            if idx == 1
            else f"/book/{book_id}/{chapter_id}_{idx}.html"
        )
