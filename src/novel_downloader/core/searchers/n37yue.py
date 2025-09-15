#!/usr/bin/env python3
"""
novel_downloader.core.searchers.n37yue
--------------------------------------

"""

from novel_downloader.core.searchers.mangg_net import ManggNetSearcher
from novel_downloader.core.searchers.registry import register_searcher


@register_searcher(
    site_keys=["n37yue"],
)
class N37yueSearcher(ManggNetSearcher):
    site_name = "n37yue"
    priority = 30
    BASE_URL = "https://www.37yue.com/"
    SEARCH_URL = "https://www.37yue.com/search.php"

    @staticmethod
    def _url_to_id(url: str) -> str:
        # "/84/84936/" -> "84-84936"
        return url.strip("/").replace("/", "-")
