#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.shuhaige
---------------------------------------

"""


from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["shuhaige"],
)
class ShuhaigeSession(GenericSession):
    """
    A session class for interacting with the
    书海阁小说网 (www.shuhaige.net) novel.
    """

    site_name: str = "shuhaige"

    BOOK_INFO_URL = "https://www.shuhaige.net/{book_id}/"
    CHAPTER_URL = "https://www.shuhaige.net/{book_id}/{chapter_id}.html"
