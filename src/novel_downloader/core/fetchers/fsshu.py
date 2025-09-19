#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.fsshu
------------------------------------

"""

from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["fsshu"],
)
class FsshuSession(GenericSession):
    """
    A session class for interacting with the 笔趣阁 (www.fsshu.com) novel.
    """

    site_name: str = "fsshu"

    BASE_URL = "https://www.fsshu.com"

    USE_PAGINATED_INFO = True
    USE_PAGINATED_CHAPTER = True

    @classmethod
    def relative_info_url(cls, book_id: str, idx: int) -> str:
        return (
            f"/biquge/{book_id}/index_{idx}.html" if idx > 1 else f"/biquge/{book_id}/"
        )

    @classmethod
    def relative_chapter_url(cls, book_id: str, chapter_id: str, idx: int) -> str:
        return (
            f"/biquge/{book_id}/{chapter_id}_{idx}.html"
            if idx > 1
            else f"/biquge/{book_id}/{chapter_id}.html"
        )
