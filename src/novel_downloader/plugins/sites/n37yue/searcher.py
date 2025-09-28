#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n37yue.searcher
----------------------------------------------

"""

from novel_downloader.plugins.searching import register_searcher
from novel_downloader.plugins.sites.mangg_net.searcher import ManggNetSearcher


@register_searcher()
class N37yueSearcher(ManggNetSearcher):
    site_name = "n37yue"
    priority = 30
    BASE_URL = "https://www.37yue.com/"
    SEARCH_URL = "https://www.37yue.com/search.php"

    @staticmethod
    def _url_to_id(url: str) -> str:
        # "/84/84936/" -> "84-84936"
        return url.strip("/").replace("/", "-")
