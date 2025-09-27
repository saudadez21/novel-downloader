#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.shencou.fetcher
----------------------------------------------

"""

from typing import Any

from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class ShencouSession(GenericSession):
    """
    A session class for interacting with the 神凑轻小说 (www.shencou.com) novel.
    """

    site_name: str = "shencou"

    BOOK_ID_REPLACEMENTS = [("-", "/")]

    HAS_SEPARATE_CATALOG: bool = True
    BOOK_INFO_URL = "https://www.shencou.com/books/read_{book_id}.html"
    BOOK_CATALOG_URL = "https://www.shencou.com/read/{book_id}/index.html"
    CHAPTER_URL = "https://www.shencou.com/read/{book_id}/{chapter_id}.html"

    @classmethod
    def book_info_url(cls, **kwargs: Any) -> str:
        if not cls.BOOK_INFO_URL:
            raise NotImplementedError(f"{cls.__name__}.BOOK_INFO_URL not set")
        book_id = kwargs["book_id"]
        clean_id = book_id.rsplit("/", 1)[-1]
        return cls.BOOK_INFO_URL.format(book_id=clean_id)
