#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n37yue.fetcher
---------------------------------------------

"""

from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class N37yueSession(GenericSession):
    """
    A session class for interacting with the 37阅读网 (www.37yue.com) novel.
    """

    site_name: str = "n37yue"

    BASE_URL = "https://www.37yue.com"
    BOOK_ID_REPLACEMENTS = [("-", "/")]

    USE_PAGINATED_INFO = True
    USE_PAGINATED_CHAPTER = True

    @classmethod
    def relative_info_url(cls, book_id: str, idx: int) -> str:
        return f"/{book_id}/index_{idx}.html" if idx > 1 else f"/{book_id}/"

    @classmethod
    def relative_chapter_url(cls, book_id: str, chapter_id: str, idx: int) -> str:
        return (
            f"/{book_id}/{chapter_id}_{idx}.html"
            if idx > 1
            else f"/{book_id}/{chapter_id}.html"
        )
