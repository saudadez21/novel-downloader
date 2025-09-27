#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.biquge5.searcher
-----------------------------------------------

"""

from novel_downloader.plugins.searching import register_searcher
from novel_downloader.plugins.sites.mangg_net.searcher import ManggNetSearcher


@register_searcher()
class Biquge5Searcher(ManggNetSearcher):
    site_name = "biquge5"
    priority = 30
    BASE_URL = "https://www.biquge5.com/"
    SEARCH_URL = "https://www.biquge5.com/search.php"

    @staticmethod
    def _url_to_id(url: str) -> str:
        # "/84_84873/" -> "84_84873"
        return url.strip("/")
