#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.lnovel.fetcher
---------------------------------------------

"""

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class LnovelFetcher(GenericFetcher):
    """
    A session class for interacting with the 轻小说百科 (lnovel.org) novel.
    """

    site_name: str = "lnovel"
    BASE_URL_MAP: dict[str, str] = {
        "simplified": "lnovel.org",
        "traditional": "lnovel.tw",
    }
    DEFAULT_BASE_URL: str = "lnovel.org"

    BOOK_INFO_URL = "https://{base_url}/books-{book_id}"
    CHAPTER_URL = "https://{base_url}/chapters-{chapter_id}"
