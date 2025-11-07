#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.akatsuki_novels.fetcher
------------------------------------------------------
"""

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class AkatsukiNovelsFetcher(GenericFetcher):
    """
    A session class for interacting with the 暁 (www.akatsuki-novels.com) novel.
    """

    site_name: str = "akatsuki_novels"

    BOOK_INFO_URL = "https://www.akatsuki-novels.com/stories/index/novel_id~{book_id}"
    CHAPTER_URL = (
        "https://www.akatsuki-novels.com/stories/view/{chapter_id}/novel_id~{book_id}"
    )
