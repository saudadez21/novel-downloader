#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.syosetu18.fetcher
------------------------------------------------
"""

from typing import Any

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import FetcherConfig


@registrar.register_fetcher()
class Syosetu18Fetcher(GenericFetcher):
    """
    A session class for interacting with the 小説家になろう (syosetu.com) novel.
    """

    site_name: str = "syosetu18"

    BASE_URL = "https://novel18.syosetu.com"
    CHAPTER_URL = "https://novel18.syosetu.com/{book_id}/{chapter_id}/"

    USE_PAGINATED_INFO = True

    def __init__(
        self,
        config: FetcherConfig,
        cookies: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> None:
        merged_cookies = dict(cookies or {})
        merged_cookies.setdefault("over18", "yes")
        super().__init__(config, merged_cookies, **kwargs)

    @classmethod
    def relative_info_url(cls, book_id: str, idx: int) -> str:
        return f"/{book_id}/?p={idx}" if idx > 1 else f"/{book_id}/"
