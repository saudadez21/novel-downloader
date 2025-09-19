#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.n71ge
------------------------------------

"""

from typing import Literal

from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["71ge", "n71ge"],
)
class N71geSession(GenericSession):
    """
    A session class for interacting with the 新吾爱文学 (www.71ge.com) novel.
    """

    site_name: str = "n71ge"

    BASE_URL = "https://www.71ge.com"
    BOOK_INFO_URL = "https://www.71ge.com/{book_id}/"

    USE_PAGINATED_CHAPTER = True

    @classmethod
    def relative_chapter_url(cls, book_id: str, chapter_id: str, idx: int) -> str:
        return (
            f"/{book_id}/{chapter_id}.html"
            if idx == 1
            else f"/{book_id}/{chapter_id}_{idx}.html"
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
        if page_type == "chapter":
            return f"{chapter_id}_{next_idx}.html" in current_html
        return False
