#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.syosetu_org.fetcher
--------------------------------------------------
"""

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class SyosetuOrgFetcher(GenericFetcher):
    """
    A session class for interacting with the ハーメルン (syosetu.org) novel.
    """

    site_name: str = "syosetu_org"

    BOOK_INFO_URL = "https://syosetu.org/novel/{book_id}/"
    CHAPTER_URL = "https://syosetu.org/novel/{book_id}/{chapter_id}.html"
