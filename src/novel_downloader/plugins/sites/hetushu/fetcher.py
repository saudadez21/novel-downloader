#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.hetushu.fetcher
----------------------------------------------

"""


from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class HetushuSession(GenericSession):
    """
    A session class for interacting with the 和图书 (www.hetushu.com) novel.
    """

    site_name: str = "hetushu"
    BASE_URL_MAP: dict[str, str] = {
        "simplified": "www.hetushu.com",
        "traditional": "www.hetubook.com",
    }
    DEFAULT_BASE_URL: str = "www.hetushu.com"

    BOOK_INFO_URL = "https://{base_url}/book/{book_id}/index.html"
    CHAPTER_URL = "https://{base_url}/book/{book_id}/{chapter_id}.html"
