#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.quanben5
---------------------------------------

"""


from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["quanben5"],
)
class Quanben5Session(GenericSession):
    """
    A session class for interacting with the 全本小说网 (quanben5.com) novel.
    """

    site_name: str = "quanben5"
    BASE_URL_MAP: dict[str, str] = {
        "simplified": "quanben5.com",
        "traditional": "big5.quanben5.com",
    }
    DEFAULT_BASE_URL: str = "quanben5.com"

    BOOK_INFO_URL = "https://{base_url}/n/{book_id}/xiaoshuo.html"
    CHAPTER_URL = "https://{base_url}/n/{book_id}/{chapter_id}.html"
