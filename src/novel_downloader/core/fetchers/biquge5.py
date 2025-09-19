#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.biquge5
--------------------------------------

"""

from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["biquge5"],
)
class Biquge5Session(GenericSession):
    """
    A session class for interacting with the 笔趣阁 (www.biquge5.com) novel.
    """

    site_name: str = "biquge5"

    BASE_URL = "https://www.biquge5.com"

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
