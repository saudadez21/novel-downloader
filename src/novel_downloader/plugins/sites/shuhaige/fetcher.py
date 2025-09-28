#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.shuhaige.fetcher
-----------------------------------------------

"""


from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class ShuhaigeSession(GenericSession):
    """
    A session class for interacting with the
    书海阁小说网 (www.shuhaige.net) novel.
    """

    site_name: str = "shuhaige"

    BOOK_INFO_URL = "https://www.shuhaige.net/{book_id}/"
    CHAPTER_URL = "https://www.shuhaige.net/{book_id}/{chapter_id}.html"
