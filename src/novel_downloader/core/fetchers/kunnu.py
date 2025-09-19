#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.kunnu
------------------------------------

"""


from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["kunnu"],
)
class KunnuSession(GenericSession):
    """
    A session class for interacting with the 鲲弩小说 (www.kunnu.com) novel.
    """

    site_name: str = "kunnu"

    BOOK_INFO_URL = "https://www.kunnu.com/{book_id}/"
    CHAPTER_URL = "https://www.kunnu.com/{book_id}/{chapter_id}.htm"
