#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.kunnu.fetcher
--------------------------------------------

"""


from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class KunnuSession(GenericSession):
    """
    A session class for interacting with the 鲲弩小说 (www.kunnu.com) novel.
    """

    site_name: str = "kunnu"

    BOOK_INFO_URL = "https://www.kunnu.com/{book_id}/"
    CHAPTER_URL = "https://www.kunnu.com/{book_id}/{chapter_id}.htm"
