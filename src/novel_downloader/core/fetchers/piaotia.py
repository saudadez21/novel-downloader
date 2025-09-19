#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.piaotia
--------------------------------------

"""


from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["piaotia"],
)
class PiaotiaSession(GenericSession):
    """
    A session class for interacting with the 飘天文学网 (www.piaotia.com) novel.
    """

    site_name: str = "piaotia"

    BOOK_ID_REPLACEMENTS = [("-", "/")]

    HAS_SEPARATE_CATALOG: bool = True
    BOOK_INFO_URL = "https://www.piaotia.com/bookinfo/{book_id}.html"
    BOOK_CATALOG_URL = "https://www.piaotia.com/html/{book_id}/index.html"
    CHAPTER_URL = "https://www.piaotia.com/html/{book_id}/{chapter_id}.html"
