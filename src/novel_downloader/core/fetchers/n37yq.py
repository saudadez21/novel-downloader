#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.n37yq
------------------------------------

"""


from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["n37yq"],
)
class N37yqSession(GenericSession):
    """
    A session class for interacting with the 三七轻小说 (www.37yq.com) novel.
    """

    site_name: str = "n37yq"

    HAS_SEPARATE_CATALOG: bool = True
    BOOK_INFO_URL = "https://www.37yq.com/lightnovel/{book_id}.html"
    BOOK_CATALOG_URL = "https://www.37yq.com/lightnovel/{book_id}/catalog"
    CHAPTER_URL = "https://www.37yq.com/lightnovel/{book_id}/{chapter_id}.html"
