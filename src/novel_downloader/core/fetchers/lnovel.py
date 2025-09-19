#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.lnovel
-------------------------------------

"""

from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["lnovel"],
)
class LnovelSession(GenericSession):
    """
    A session class for interacting with the 轻小说百科 (lnovel.org) novel.
    """

    site_name: str = "lnovel"
    BASE_URL_MAP: dict[str, str] = {
        "simplified": "lnovel.org",
        "traditional": "lnovel.tw",
    }
    DEFAULT_BASE_URL: str = "lnovel.org"

    BOOK_INFO_URL = "https://{base_url}/books-{book_id}"
    CHAPTER_URL = "https://{base_url}/chapters-{chapter_id}"
