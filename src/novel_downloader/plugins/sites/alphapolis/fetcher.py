#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.alphapolis.fetcher
-------------------------------------------------
"""

from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class AlphapolisSession(GenericSession):
    """
    A session class for interacting with the アルファポリス (www.alphapolis.co.jp) novel
    """

    site_name: str = "alphapolis"

    BOOK_ID_REPLACEMENTS = [("-", "/")]

    BOOK_INFO_URL = "https://www.alphapolis.co.jp/novel/{book_id}"
    CHAPTER_URL = "https://www.alphapolis.co.jp/novel/{book_id}/episode/{chapter_id}"
