#!/usr/bin/env python3
"""
novel_downloader.core.fetchers.zhenhunxiaoshuo
----------------------------------------------

"""


from novel_downloader.core.fetchers.base import GenericSession
from novel_downloader.core.fetchers.registry import register_fetcher


@register_fetcher(
    site_keys=["zhenhunxiaoshuo"],
)
class ZhenhunxiaoshuoSession(GenericSession):
    """
    A session class for interacting with the 镇魂小说网
    (www.zhenhunxiaoshuo.com) novel.
    """

    site_name: str = "zhenhunxiaoshuo"

    BOOK_INFO_URL = "https://www.zhenhunxiaoshuo.com/{book_id}/"
    CHAPTER_URL = "https://www.zhenhunxiaoshuo.com/{chapter_id}.html"
