#!/usr/bin/env python3
"""
novel_downloader.core.searchers.wanbengo
----------------------------------------

"""

from novel_downloader.core.searchers.registry import register_searcher
from novel_downloader.core.searchers.sososhu import SososhuSearcher


@register_searcher(
    site_keys=["wanbengo"],
)
class WanbengoSearcher(SososhuSearcher):
    site_name = "wanbengo"
    SOSOSHU_KEY = "wbsz"
    BASE_URL = "https://www.wanbengo.com"

    @staticmethod
    def _restore_url(url: str) -> str:
        return url.replace("www.wbsz.org", "www.wanbengo.com")

    @staticmethod
    def _url_to_id(url: str) -> str:
        return url.split("wanbengo.com", 1)[-1].strip("/")
