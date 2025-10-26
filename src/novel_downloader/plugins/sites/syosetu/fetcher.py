#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.syosetu.fetcher
----------------------------------------------
"""

from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class SyosetuSession(GenericSession):
    """
    A session class for interacting with the 小説家になろう (syosetu.com) novel.
    """

    site_name: str = "syosetu"

    BASE_URL = "https://ncode.syosetu.com"
    CHAPTER_URL = "https://ncode.syosetu.com/{book_id}/{chapter_id}/"

    USE_PAGINATED_INFO = True

    @classmethod
    def relative_info_url(cls, book_id: str, idx: int) -> str:
        return f"/{book_id}/?p={idx}" if idx > 1 else f"/{book_id}/"
