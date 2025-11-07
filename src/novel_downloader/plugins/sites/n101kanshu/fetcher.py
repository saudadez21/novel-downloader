#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n101kanshu.fetcher
-------------------------------------------------
"""

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class N101kanshuFetcher(GenericFetcher):
    """
    A session class for interacting with the 101看书 (101kanshu.com) novel.
    """

    site_name: str = "n101kanshu"

    HAS_SEPARATE_CATALOG: bool = True
    BOOK_INFO_URL = "https://101kanshu.com/book/{book_id}.html"
    BOOK_CATALOG_URL = "https://101kanshu.com/ajax_novels/chapterlist/{book_id}.html"
    CHAPTER_URL = "https://101kanshu.com/txt/{book_id}/{chapter_id}.html"
