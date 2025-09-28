#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.trxs.fetcher
-------------------------------------------

"""

from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class TrxsSession(GenericSession):
    """
    A session class for interacting with the 同人小说网 (www.trxs.cc) novel.
    """

    site_name: str = "trxs"

    BOOK_INFO_URL = "https://www.trxs.cc/tongren/{book_id}.html"
    CHAPTER_URL = "https://www.trxs.cc/tongren/{book_id}/{chapter_id}.html"
