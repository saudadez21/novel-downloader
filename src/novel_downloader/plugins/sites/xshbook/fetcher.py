#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.xshbook.fetcher
----------------------------------------------

"""

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class XshbookFetcher(GenericFetcher):
    """
    A session class for interacting with the 小说虎 (www.xshbook.com) novel.
    """

    site_name: str = "xshbook"

    BOOK_ID_REPLACEMENTS = [("-", "/")]

    BOOK_INFO_URL = "https://www.xshbook.com/{book_id}/"
    CHAPTER_URL = "https://www.xshbook.com/{book_id}/{chapter_id}.html"
