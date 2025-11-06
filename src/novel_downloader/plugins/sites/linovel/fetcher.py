#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.linovel.fetcher
----------------------------------------------
"""

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class LinovelFetcher(GenericFetcher):
    """
    A session class for interacting with the 轻之文库 (www.linovel.net) novel.
    """

    site_name: str = "linovel"

    BOOK_INFO_URL = "https://www.linovel.net/book/{book_id}.html"
    CHAPTER_URL = "https://www.linovel.net/book/{book_id}/{chapter_id}.html"
