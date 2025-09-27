#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.yibige.fetcher
---------------------------------------------

"""


from novel_downloader.plugins.base.fetcher import GenericSession
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class YibigeSession(GenericSession):
    """
    A session class for interacting with the 一笔阁 (www.yibige.org) novel.
    """

    site_name: str = "yibige"
    BASE_URL_MAP: dict[str, str] = {
        "simplified": "www.yibige.org",  # 主站
        "traditional": "tw.yibige.org",
        "singapore": "sg.yibige.org",  # 新加坡
        "taiwan": "tw.yibige.org",  # 臺灣正體
        "hongkong": "hk.yibige.org",  # 香港繁體
    }
    DEFAULT_BASE_URL: str = "www.yibige.org"

    HAS_SEPARATE_CATALOG: bool = True
    BOOK_INFO_URL = "https://{base_url}/{book_id}/"
    BOOK_CATALOG_URL = "https://{base_url}/{book_id}/index.html"
    CHAPTER_URL = "https://{base_url}/{book_id}/{chapter_id}.html"
