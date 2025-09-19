#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.i25zw
------------------------------------

"""


from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["i25zw"],
)
class I25zwSession(GenericSession):
    """
    A session class for interacting with the 25中文网 (www.i25zw.com) novel.
    """

    site_name: str = "i25zw"

    HAS_SEPARATE_CATALOG: bool = True
    BOOK_INFO_URL = "https://www.i25zw.com/book/{book_id}.html"
    BOOK_CATALOG_URL = "https://www.i25zw.com/{book_id}/"
    CHAPTER_URL = "https://www.i25zw.com/{book_id}/{chapter_id}.html"
