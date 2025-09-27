#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.biquyuedu.fetcher
------------------------------------------------

"""


from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class BiquyueduSession(GenericSession):
    """
    A session class for interacting with the 精彩小说 (biquyuedu.com) novel.
    """

    site_name: str = "biquyuedu"

    BOOK_INFO_URL = "https://biquyuedu.com/novel/{book_id}.html"
    CHAPTER_URL = "https://biquyuedu.com/novel/{book_id}/{chapter_id}.html"
