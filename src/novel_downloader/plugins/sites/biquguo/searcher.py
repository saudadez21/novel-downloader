#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.biquguo.searcher
-----------------------------------------------

"""

from novel_downloader.plugins.searching import register_searcher
from novel_downloader.plugins.sites.mangg_net.searcher import ManggNetSearcher


@register_searcher()
class BiquguoSearcher(ManggNetSearcher):
    site_name = "biquguo"
    priority = 30
    BASE_URL = "https://www.biquguo.com/"
    SEARCH_URL = "https://www.biquguo.com/search.php"

    @staticmethod
    def _url_to_id(url: str) -> str:
        # "/84/84829/" -> "84-84829"
        return url.strip("/").replace("/", "-")
