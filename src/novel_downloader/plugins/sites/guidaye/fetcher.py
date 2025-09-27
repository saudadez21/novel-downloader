#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.guidaye.fetcher
----------------------------------------------

"""


from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class GuidayeSession(GenericSession):
    """
    A session class for interacting with the 名著阅读 (b.guidaye.com) novel.
    """

    site_name: str = "guidaye"

    BOOK_ID_REPLACEMENTS = [("-", "/")]

    BOOK_INFO_URL = "https://b.guidaye.com/{book_id}/"
    CHAPTER_URL = "https://b.guidaye.com/{book_id}/{chapter_id}.html"
