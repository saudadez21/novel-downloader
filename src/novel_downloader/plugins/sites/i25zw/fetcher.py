#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.i25zw.fetcher
--------------------------------------------

"""


from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class I25zwSession(GenericSession):
    """
    A session class for interacting with the 25中文网 (www.i25zw.com) novel.
    """

    site_name: str = "i25zw"

    HAS_SEPARATE_CATALOG: bool = True
    BOOK_INFO_URL = "https://www.i25zw.com/book/{book_id}.html"
    BOOK_CATALOG_URL = "https://www.i25zw.com/{book_id}/"
    CHAPTER_URL = "https://www.i25zw.com/{book_id}/{chapter_id}.html"
