#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.zhenhunxiaoshuo.fetcher
------------------------------------------------------

"""

from novel_downloader.plugins.base.fetcher import GenericFetcher
from novel_downloader.plugins.registry import registrar


@registrar.register_fetcher()
class ZhenhunxiaoshuoFetcher(GenericFetcher):
    """
    A session class for interacting with the 镇魂小说网
    (www.zhenhunxiaoshuo.com) novel.
    """

    site_name: str = "zhenhunxiaoshuo"

    BOOK_INFO_URL = "https://www.zhenhunxiaoshuo.com/{book_id}/"
    CHAPTER_URL = "https://www.zhenhunxiaoshuo.com/{chapter_id}.html"
