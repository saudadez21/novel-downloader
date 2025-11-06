#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.tongrenquan.fetcher
--------------------------------------------------

"""

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class TongrenquanFetcher(GenericFetcher):
    """
    A session class for interacting with the 同人圈 (www.tongrenquan.org) novel.
    """

    site_name: str = "tongrenquan"

    BOOK_INFO_URL = "https://www.tongrenquan.org/tongren/{book_id}.html"
    CHAPTER_URL = "https://www.tongrenquan.org/tongren/{book_id}/{chapter_id}.html"
