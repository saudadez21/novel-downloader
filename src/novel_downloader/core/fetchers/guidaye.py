#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.guidaye
--------------------------------------

"""


from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["guidaye"],
)
class GuidayeSession(GenericSession):
    """
    A session class for interacting with the 名著阅读 (b.guidaye.com) novel.
    """

    site_name: str = "guidaye"

    BOOK_ID_REPLACEMENTS = [("-", "/")]

    BOOK_INFO_URL = "https://b.guidaye.com/{book_id}/"
    CHAPTER_URL = "https://b.guidaye.com/{book_id}/{chapter_id}.html"
