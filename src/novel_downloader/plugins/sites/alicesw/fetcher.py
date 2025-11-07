#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.alicesw.fetcher
----------------------------------------------
"""

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class AliceswFetcher(GenericFetcher):
    """
    A session class for interacting with the 爱丽丝书屋 (www.alicesw.com) novel.
    """

    site_name: str = "alicesw"

    BOOK_ID_REPLACEMENTS = [("-", "/")]
    CHAP_ID_REPLACEMENTS = [("-", "/")]

    HAS_SEPARATE_CATALOG: bool = True
    BOOK_INFO_URL = "https://www.alicesw.com/novel/{book_id}.html"
    BOOK_CATALOG_URL = "https://www.alicesw.com/other/chapters/id/{book_id}.html"
    CHAPTER_URL = "https://www.alicesw.com/book/{chapter_id}.html"
