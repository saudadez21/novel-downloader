#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.tongrenshe.fetcher
-------------------------------------------------
"""

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class TongrensheFetcher(GenericFetcher):
    """
    A session class for interacting with the 同人社 (tongrenshe.cc) novel.
    """

    site_name: str = "tongrenshe"

    BOOK_INFO_URL = "https://tongrenshe.cc/tongren/{book_id}.html"
    CHAPTER_URL = "https://tongrenshe.cc/tongren/{book_id}/{chapter_id}.html"
