#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.biquyuedu
----------------------------------------

"""


from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["biquyuedu"],
)
class BiquyueduSession(GenericSession):
    """
    A session class for interacting with the 精彩小说 (biquyuedu.com) novel.
    """

    site_name: str = "biquyuedu"

    BOOK_INFO_URL = "https://biquyuedu.com/novel/{book_id}.html"
    CHAPTER_URL = "https://biquyuedu.com/novel/{book_id}/{chapter_id}.html"
