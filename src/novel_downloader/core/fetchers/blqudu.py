#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.blqudu
-------------------------------------

"""

from novel_downloader.core.fetchers.lewenn import LewennSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["blqudu"],
)
class BlquduSession(LewennSession):
    """
    A session class for interacting with the 笔趣读 (www.blqudu.cc) novel website.
    """

    site_name: str = "blqudu"

    BOOK_INFO_URL = "https://www.blqudu.cc/{book_id}/"
    CHAPTER_URL = "https://www.biqudv.cc/{book_id}/{chapter_id}.html"
