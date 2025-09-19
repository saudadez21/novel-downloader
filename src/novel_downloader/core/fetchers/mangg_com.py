#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.mangg_com
----------------------------------------

"""

from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["mangg_com"],
)
class ManggComSession(GenericSession):
    """
    A session class for interacting with the 追书网 (www.mangg.com) novel.
    """

    site_name: str = "mangg_com"

    BOOK_INFO_URL = "https://www.mangg.com/{book_id}/"
    CHAPTER_URL = "https://www.mangg.com/{book_id}/{chapter_id}.html"
