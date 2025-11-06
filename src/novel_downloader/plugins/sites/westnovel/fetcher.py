#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.westnovel.fetcher
------------------------------------------------
"""

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class WestnovelFetcher(GenericFetcher):
    """
    A session class for interacting with the 西方奇幻小说网 (www.westnovel.com) novel.
    """

    site_name: str = "westnovel"
    BOOK_ID_REPLACEMENTS = [("-", "/")]

    BOOK_INFO_URL = "https://www.westnovel.com/{book_id}/"
    CHAPTER_URL = "https://www.westnovel.com/{book_id}/{chapter_id}.html"
