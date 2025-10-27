#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.pilibook.fetcher
-----------------------------------------------
"""

from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class PilibookSession(GenericSession):
    """
    A session class for interacting with the 霹雳书屋 (www.pilibook.net) novel.
    """

    site_name: str = "pilibook"

    BOOK_ID_REPLACEMENTS = [("-", "/")]

    HAS_SEPARATE_CATALOG: bool = True
    BOOK_INFO_URL = "https://www.pilibook.net/{book_id}/info.html"
    BOOK_CATALOG_URL = "https://www.pilibook.net/{book_id}/menu/1.html"
    CHAPTER_URL = "https://www.pilibook.net/{book_id}/read/{chapter_id}.html"
