#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.dushu.fetcher
--------------------------------------------
"""

import logging

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar

logger = logging.getLogger(__name__)


@registrar.register_fetcher()
class DushuFetcher(GenericFetcher):
    """
    A session class for interacting with the 读书 (www.dushu.com) novel.
    """

    site_name: str = "dushu"

    BOOK_INFO_URL = "https://www.dushu.com/showbook/{book_id}/"
    CHAPTER_URL = "https://www.dushu.com/showbook/{book_id}/{chapter_id}.html"

    IMAGE_HEADERS = {
        **GenericFetcher.IMAGE_HEADERS,
        "Referer": "https://www.dushu.com/",
    }
