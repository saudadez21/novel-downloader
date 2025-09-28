#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.shu111.fetcher
---------------------------------------------

"""


from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class Shu111Session(GenericSession):
    """
    A session class for interacting with the 书林文学 (shu111.com) novel.
    """

    site_name: str = "shu111"

    BOOK_INFO_URL = "http://www.shu111.com/book/{book_id}.html"
    CHAPTER_URL = "http://www.shu111.com/book/{book_id}/{chapter_id}.html"
