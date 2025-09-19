#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.trxs
-----------------------------------

"""

from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["trxs"],
)
class TrxsSession(GenericSession):
    """
    A session class for interacting with the 同人小说网 (www.trxs.cc) novel.
    """

    site_name: str = "trxs"

    BOOK_INFO_URL = "https://www.trxs.cc/tongren/{book_id}.html"
    CHAPTER_URL = "https://www.trxs.cc/tongren/{book_id}/{chapter_id}.html"
