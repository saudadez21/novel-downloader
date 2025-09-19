#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.lewenn
-------------------------------------

"""

from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["lewenn", "lewen"],
)
class LewennSession(GenericSession):
    """
    A session class for interacting with the 乐文小说网 (www.lewenn.net) novel.
    """

    site_name: str = "lewenn"

    BOOK_INFO_URL = "https://www.lewenn.net/{book_id}/"
    CHAPTER_URL = "https://www.lewenn.net/{book_id}/{chapter_id}.html"
