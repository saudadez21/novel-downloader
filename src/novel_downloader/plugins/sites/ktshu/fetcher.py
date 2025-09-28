#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ktshu.fetcher
--------------------------------------------

"""

from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class KtshuSession(GenericSession):
    """
    A session class for interacting with the 八一中文网 (www.ktshu.cc) novel.
    """

    site_name: str = "ktshu"

    BASE_URL = "https://www.ktshu.cc"

    USE_PAGINATED_INFO = True
    USE_PAGINATED_CHAPTER = True

    @classmethod
    def relative_info_url(cls, book_id: str, idx: int) -> str:
        return f"/book/{book_id}/index_{idx}.html" if idx > 1 else f"/book/{book_id}/"

    @classmethod
    def relative_chapter_url(cls, book_id: str, chapter_id: str, idx: int) -> str:
        return (
            f"/book/{book_id}/{chapter_id}_{idx}.html"
            if idx > 1
            else f"/book/{book_id}/{chapter_id}.html"
        )
