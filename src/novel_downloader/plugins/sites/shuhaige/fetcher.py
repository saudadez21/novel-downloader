#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.shuhaige.fetcher
-----------------------------------------------

"""

from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class ShuhaigeSession(GenericSession):
    """
    A session class for interacting with the
    书海阁小说网 (www.shuhaige.net) novel.
    """

    site_name: str = "shuhaige"

    BASE_URL = "https://www.shuhaige.net"
    BOOK_INFO_URL = "https://www.shuhaige.net/{book_id}/"

    USE_PAGINATED_CHAPTER = True

    @classmethod
    def relative_chapter_url(cls, book_id: str, chapter_id: str, idx: int) -> str:
        return (
            f"/{book_id}/{chapter_id}_{idx}.html"
            if idx > 1
            else f"/{book_id}/{chapter_id}.html"
        )
