#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.bxwx9
------------------------------------

"""

from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["bxwx9"],
)
class Bxwx9Session(GenericSession):
    """
    A session class for interacting with the 笔下文学网 (www.bxwx9.org) novel.
    """

    site_name: str = "bxwx9"

    BASE_URL = "https://www.bxwx9.org"
    BOOK_ID_REPLACEMENTS = [("-", "/")]

    USE_PAGINATED_INFO = True
    USE_PAGINATED_CHAPTER = True

    @classmethod
    def relative_info_url(cls, book_id: str, idx: int) -> str:
        return f"/b/{book_id}/index_{idx}.html" if idx > 1 else f"/b/{book_id}/"

    @classmethod
    def relative_chapter_url(cls, book_id: str, chapter_id: str, idx: int) -> str:
        return (
            f"/b/{book_id}/{chapter_id}_{idx}.html"
            if idx > 1
            else f"/b/{book_id}/{chapter_id}.html"
        )
