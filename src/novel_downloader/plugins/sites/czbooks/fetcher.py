#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.czbooks.fetcher
----------------------------------------------
"""

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class CzbooksFetcher(GenericFetcher):
    """
    A session class for interacting with the 小说狂人 (czbooks.net) novel.
    """

    site_name: str = "czbooks"

    BOOK_INFO_URL = "https://czbooks.net/n/{book_id}"
    CHAPTER_URL = "https://czbooks.net/n/{book_id}/{chapter_id}"
