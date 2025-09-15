#!/usr/bin/env python3
"""
novel_downloader.core.searchers.biquguo
---------------------------------------

"""

from novel_downloader.core.searchers.mangg_net import ManggNetSearcher
from novel_downloader.core.searchers.registry import register_searcher


@register_searcher(
    site_keys=["biquguo"],
)
class BiquguoSearcher(ManggNetSearcher):
    site_name = "biquguo"
    priority = 30
    BASE_URL = "https://www.biquguo.com/"
    SEARCH_URL = "https://www.biquguo.com/search.php"

    @staticmethod
    def _url_to_id(url: str) -> str:
        # "/84/84829/" -> "84-84829"
        return url.strip("/").replace("/", "-")
