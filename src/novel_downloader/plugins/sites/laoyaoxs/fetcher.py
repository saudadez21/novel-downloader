#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.laoyaoxs.fetcher
-----------------------------------------------

"""


from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class LaoyaoxsSession(GenericSession):
    """
    A session class for interacting with the 老幺小说网 (www.laoyaoxs.org) novel.
    """

    site_name: str = "laoyaoxs"

    HAS_SEPARATE_CATALOG: bool = True
    BOOK_INFO_URL = "https://www.laoyaoxs.org/info/{book_id}.html"
    BOOK_CATALOG_URL = "https://www.laoyaoxs.org/list/{book_id}/"
    CHAPTER_URL = "https://www.laoyaoxs.org/list/{book_id}/{chapter_id}.html"
