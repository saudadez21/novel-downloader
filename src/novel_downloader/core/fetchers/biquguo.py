#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.biquguo
--------------------------------------

"""

from novel_downloader.core.fetchers.mangg_net import ManggNetSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["biquguo"],
)
class XXSession(ManggNetSession):
    """
    A session class for interacting with the 笔趣阁小说网 (www.biquguo.com) novel.
    """

    site_name: str = "biquguo"

    BASE_URL = "https://www.biquguo.com"

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
