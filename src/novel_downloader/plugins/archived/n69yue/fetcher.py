#!/usr/bin/env python3
"""
novel_downloader.plugins.archived.n69yue.fetcher
------------------------------------------------

"""

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class N69yueFetcher(GenericFetcher):
    """
    A session class for interacting with the 69阅读 (www.69yue.top) novel.
    """

    site_name: str = "n69yue"

    HAS_SEPARATE_CATALOG: bool = True
    BOOK_INFO_URL = "https://www.69yue.top/articlecategroy/{book_id}.html"
    BOOK_CATALOG_URL = "https://www.69yue.top/api/articleitems/{book_id}.json"
    CHAPTER_URL = "https://www.69yue.top/article/{chapter_id}.html"
