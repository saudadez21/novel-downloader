#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.mangg_com.fetcher
------------------------------------------------

"""

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class ManggComFetcher(GenericFetcher):
    """
    A session class for interacting with the 追书网 (www.mangg.com) novel.
    """

    site_name: str = "mangg_com"

    BOOK_INFO_URL = "https://www.mangg.com/{book_id}/"
    CHAPTER_URL = "https://www.mangg.com/{book_id}/{chapter_id}.html"
