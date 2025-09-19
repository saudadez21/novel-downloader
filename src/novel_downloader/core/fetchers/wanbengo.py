#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.wanbengo
---------------------------------------

"""


from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["wanbengo"],
)
class WanbengoSession(GenericSession):
    """
    A session class for interacting with the 完本神站 (www.wanbengo.com) novel.
    """

    site_name: str = "wanbengo"

    BOOK_INFO_URL = "https://www.wanbengo.com/{book_id}/"
    CHAPTER_URL = "https://www.wanbengo.com/{book_id}/{chapter_id}.html"
