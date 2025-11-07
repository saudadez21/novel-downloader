#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.westnovel_sub.fetcher
----------------------------------------------------
"""

from typing import Any

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class WestnovelSubFetcher(GenericFetcher):
    """
    A session class for interacting with the 西方奇幻小说网 (www.westnovel.com) novel.
    """

    site_name: str = "westnovel_sub"
    BOOK_ID_REPLACEMENTS = [("-", "/")]

    BOOK_INFO_URL = "https://www.westnovel.com/{book_id}.html"
    CHAPTER_URL = "https://www.westnovel.com/{prefix}/showinfo-{chapter_id}.html"

    @classmethod
    def chapter_url(cls, **kwargs: Any) -> str:
        if not cls.CHAPTER_URL:
            raise NotImplementedError(f"{cls.__name__}.CHAPTER_URL not set")

        book_id: str | None = kwargs.get("book_id")
        chapter_id: str | None = kwargs.get("chapter_id")

        if not book_id or "/" not in book_id:
            raise ValueError(f"Invalid book_id: {book_id!r}")
        if not chapter_id:
            raise ValueError("Missing chapter_id in kwargs")

        prefix = book_id.split("/", 1)[0]
        return cls.CHAPTER_URL.format(prefix=prefix, chapter_id=chapter_id)
