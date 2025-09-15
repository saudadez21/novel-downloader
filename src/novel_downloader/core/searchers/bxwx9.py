#!/usr/bin/env python3
"""
novel_downloader.core.searchers.bxwx9
-------------------------------------

"""

from novel_downloader.core.searchers.mangg_net import ManggNetSearcher
from novel_downloader.core.searchers.registry import register_searcher


@register_searcher(
    site_keys=["bxwx9"],
)
class Bxwx9Searcher(ManggNetSearcher):
    site_name = "bxwx9"
    priority = 30
    BASE_URL = "https://www.bxwx9.org/"
    SEARCH_URL = "https://www.bxwx9.org/search.php"

    @staticmethod
    def _url_to_id(url: str) -> str:
        # "/b/70/70316/" -> "70-70316"
        parts = url.strip("/").split("/")
        return "-".join(parts[1:])
