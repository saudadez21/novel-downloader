#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.biquge345.fetcher
------------------------------------------------
"""

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class Biquge345Fetcher(GenericFetcher):
    """
    A session class for interacting with the 笔趣阁 (www.biquge345.com) novel.
    """

    site_name: str = "biquge345"

    BOOK_INFO_URL = "https://www.biquge345.com/book/{book_id}/"
    CHAPTER_URL = "https://www.biquge345.com/chapter/{book_id}/{chapter_id}.html"
