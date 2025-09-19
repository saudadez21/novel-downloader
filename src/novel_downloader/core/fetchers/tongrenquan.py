#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.tongrenquan
------------------------------------------

"""


from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["tongrenquan"],
)
class TongrenquanSession(GenericSession):
    """
    A session class for interacting with the 同人圈 (www.tongrenquan.org) novel.
    """

    site_name: str = "tongrenquan"

    BOOK_INFO_URL = "https://www.tongrenquan.org/tongren/{book_id}.html"
    CHAPTER_URL = "https://www.tongrenquan.org/tongren/{book_id}/{chapter_id}.html"
