#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.xshbook
--------------------------------------

"""


from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["xshbook"],
)
class XshbookSession(GenericSession):
    """
    A session class for interacting with the 小说虎 (www.xshbook.com) novel.
    """

    site_name: str = "xshbook"

    BOOK_ID_REPLACEMENTS = [("-", "/")]

    BOOK_INFO_URL = "https://www.xshbook.com/{book_id}/"
    CHAPTER_URL = "https://www.xshbook.com/{book_id}/{chapter_id}.html"
