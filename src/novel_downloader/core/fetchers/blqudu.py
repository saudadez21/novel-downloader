#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.blqudu
-------------------------------------

"""

from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["blqudu"],
)
class BlquduSession(GenericSession):
    """
    A session class for interacting with the 笔趣读 (www.blqudu.cc) novel.
    """

    site_name: str = "blqudu"

    BOOK_INFO_URL = "https://www.blqudu.cc/{book_id}/"
    CHAPTER_URL = "https://www.biqudv.cc/{book_id}/{chapter_id}.html"
