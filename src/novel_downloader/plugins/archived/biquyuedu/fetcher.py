#!/usr/bin/env python3
"""
novel_downloader.plugins.archived.biquyuedu.fetcher
---------------------------------------------------

"""

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class BiquyueduFetcher(GenericFetcher):
    """
    A session class for interacting with the 精彩小说 (biquyuedu.com) novel.
    """

    site_name: str = "biquyuedu"

    BOOK_INFO_URL = "https://biquyuedu.com/novel/{book_id}.html"
    CHAPTER_URL = "https://biquyuedu.com/novel/{book_id}/{chapter_id}.html"
