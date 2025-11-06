#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.fanqienovel.fetcher
--------------------------------------------------
"""


from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class FanqienovelFetcher(GenericFetcher):
    """
    A session class for interacting with the 番茄小说网 (fanqienovel.com) novel.
    """

    site_name: str = "fanqienovel"

    BOOK_INFO_URL = "https://fanqienovel.com/page/{book_id}"
    CHAPTER_URL = "https://fanqienovel.com/reader/{chapter_id}"
