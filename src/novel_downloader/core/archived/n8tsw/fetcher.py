#!/usr/bin/env python3
"""
novel_downloader.core.archived.n8tsw.fetcher
--------------------------------------------

"""

from novel_downloader.core.fetchers.registry import register_fetcher
from novel_downloader.core.fetchers.shuhaige import ShuhaigeSession


@register_fetcher(
    site_keys=["n8tsw"],
)
class N8tswSession(ShuhaigeSession):
    """
    A session class for interacting with the 笔趣阁 (www.8tsw.com) novel.
    """

    site_name: str = "n8tsw"

    BOOK_INFO_URL = "https://www.8tsw.com/{book_id}/"
    CHAPTER_URL = "https://www.8tsw.com/{book_id}/{chapter_id}.html"
