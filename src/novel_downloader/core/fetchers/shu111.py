#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.shu111
-------------------------------------

"""


from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["shu111"],
)
class Shu111Session(GenericSession):
    """
    A session class for interacting with the 书林文学 (shu111.com) novel.
    """

    site_name: str = "shu111"

    BOOK_INFO_URL = "http://www.shu111.com/book/{book_id}.html"
    CHAPTER_URL = "http://www.shu111.com/book/{book_id}/{chapter_id}.html"
