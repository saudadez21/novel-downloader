#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.wanbengo.fetcher
-----------------------------------------------

"""


from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class WanbengoSession(GenericSession):
    """
    A session class for interacting with the 完本神站 (www.wanbengo.com) novel.
    """

    site_name: str = "wanbengo"

    BOOK_INFO_URL = "https://www.wanbengo.com/{book_id}/"
    CHAPTER_URL = "https://www.wanbengo.com/{book_id}/{chapter_id}.html"
