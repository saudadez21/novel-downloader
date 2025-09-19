#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.n23qb
------------------------------------

"""


from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["n23qb"],
)
class N23qbSession(GenericSession):
    """
    A session class for interacting with the 铅笔小说 (www.23qb.com) novel.
    """

    site_name: str = "n23qb"

    HAS_SEPARATE_CATALOG: bool = True
    BOOK_INFO_URL = "https://www.23qb.com/book/{book_id}/"
    BOOK_CATALOG_URL = "https://www.23qb.com/book/{book_id}/catalog"
    CHAPTER_URL = "https://www.23qb.com/book/{book_id}/{chapter_id}.html"
