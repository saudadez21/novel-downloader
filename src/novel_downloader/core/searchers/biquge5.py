#!/usr/bin/env python3
"""
novel_downloader.core.searchers.biquge5
---------------------------------------

"""

from novel_downloader.core.searchers.mangg_net import ManggNetSearcher
from novel_downloader.core.searchers.registry import register_searcher


@register_searcher(
    site_keys=["biquge5"],
)
class Biquge5Searcher(ManggNetSearcher):
    site_name = "biquge5"
    priority = 30
    BASE_URL = "https://www.biquge5.com/"
    SEARCH_URL = "https://www.biquge5.com/search.php"

    @staticmethod
    def _url_to_id(url: str) -> str:
        # "/84_84873/" -> "84_84873"
        return url.strip("/")
