#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.mangg_net
----------------------------------------

"""


from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["mangg_net"],
)
class ManggNetSession(GenericSession):
    """
    A session class for interacting with the 追书网 (www.mangg.net) novel.
    """

    site_name: str = "mangg_net"

    BASE_URL = "https://www.mangg.net"
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
