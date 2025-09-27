#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.wanbengo.searcher
------------------------------------------------

"""

from novel_downloader.plugins.searching import register_searcher
from novel_downloader.plugins.sites.sososhu.searcher import SososhuSearcher


@register_searcher()
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
