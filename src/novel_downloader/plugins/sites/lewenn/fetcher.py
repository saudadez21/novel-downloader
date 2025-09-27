#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.lewenn.fetcher
---------------------------------------------

"""

from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class LewennSession(GenericSession):
    """
    A session class for interacting with the 乐文小说网 (www.lewenn.net) novel.
    """

    site_name: str = "lewenn"

    BOOK_INFO_URL = "https://www.lewenn.net/{book_id}/"
    CHAPTER_URL = "https://www.lewenn.net/{book_id}/{chapter_id}.html"
