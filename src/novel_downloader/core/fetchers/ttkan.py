#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.ttkan
------------------------------------

"""

from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["ttkan"],
)
class TtkanSession(GenericSession):
    """
    A session class for interacting with the 天天看小说 (www.ttkan.co) novel.
    """

    site_name: str = "ttkan"

    BASE_URL_MAP: dict[str, str] = {
        "simplified": "cn",
        "traditional": "tw",
    }
    DEFAULT_BASE_URL: str = "cn"

    BOOK_INFO_URL = "https://{base_url}.ttkan.co/novel/chapters/{book_id}"
    CHAPTER_URL = "https://{base_url}.wa01.com/novel/pagea/{book_id}_{chapter_id}.html"
