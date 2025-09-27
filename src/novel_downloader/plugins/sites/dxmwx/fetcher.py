#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.dxmwx.fetcher
--------------------------------------------

"""


from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class DxmwxSession(GenericSession):
    """
    A session class for interacting with the 大熊猫文学网 (www.dxmwx.org) novel.
    """

    site_name: str = "dxmwx"
    BASE_URL_MAP: dict[str, str] = {
        "simplified": "www.dxmwx.org",
        "traditional": "tw.dxmwx.org",
    }
    DEFAULT_BASE_URL: str = "www.dxmwx.org"

    HAS_SEPARATE_CATALOG: bool = True
    BOOK_INFO_URL = "https://{base_url}/book/{book_id}.html"
    BOOK_CATALOG_URL = "https://{base_url}/chapter/{book_id}.html"
    CHAPTER_URL = "https://{base_url}/read/{book_id}_{chapter_id}.html"
