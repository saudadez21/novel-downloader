#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.xiguashuwu.fetcher
-------------------------------------------------

"""

from typing import Literal

from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class XiguashuwuSession(GenericSession):
    """
    A session class for interacting with the 西瓜书屋 (www.xiguashuwu.com) novel.
    """

    site_name: str = "xiguashuwu"

    HAS_SEPARATE_CATALOG = True
    BASE_URL = "https://www.xiguashuwu.com"
    BOOK_INFO_URL = "https://www.xiguashuwu.com/book/{book_id}/iszip/0/"
    BOOK_CATALOG_URL = "https://www.xiguashuwu.com/book/{book_id}/catalog/"
    CHAPTER_URL = "https://www.xiguashuwu.com/book/{book_id}/{chapter_id}.html"

    USE_PAGINATED_CATALOG = True
    USE_PAGINATED_CHAPTER = True

    @classmethod
    def relative_catalog_url(cls, book_id: str, idx: int) -> str:
        return (
            f"/book/{book_id}/catalog/"
            if idx == 1
            else f"/book/{book_id}/catalog/{idx}.html"
        )

    @classmethod
    def relative_chapter_url(cls, book_id: str, chapter_id: str, idx: int) -> str:
        return (
            f"/book/{book_id}/{chapter_id}.html"
            if idx == 1
            else f"/book/{book_id}/{chapter_id}_{idx}.html"
        )

    def should_continue_pagination(
        self,
        current_html: str,
        next_suffix: str,
        next_idx: int,
        page_type: Literal["info", "catalog", "chapter"],
        book_id: str,
        chapter_id: str | None = None,
    ) -> bool:
        if page_type == "catalog":
            next_patterns = [
                f"javascript:readbookjump('{book_id}','{next_idx}');",
                f"javascript:gobookjump('{book_id}','{next_idx}');",
                f"javascript:runbookjump('{book_id}','{next_idx}');",
                f"javascript:gotojump('{book_id}','{next_idx}');",
                f"javascript:gotochapterjump('{book_id}','{next_idx}');",
                f"/book/{book_id}/catalog/{next_idx}.html",
            ]
            return any(pat in current_html for pat in next_patterns)

        if page_type == "chapter":
            return next_suffix in current_html

        return False
