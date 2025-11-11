#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.tianyabooks.fetcher
--------------------------------------------------
"""

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class TianyabooksFetcher(GenericFetcher):
    """
    A session class for interacting with the 天涯书库 (www.tianyabooks.com) novel
    """

    site_name: str = "tianyabooks"

    BOOK_ID_REPLACEMENTS = [("-", "/")]

    BOOK_INFO_URL = "https://www.tianyabooks.com/{book_id}/"
    CHAPTER_URL = "https://www.tianyabooks.com/{book_id}/{chapter_id}.html"
