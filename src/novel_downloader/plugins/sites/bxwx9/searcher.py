#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.bxwx9.searcher
---------------------------------------------

"""

from novel_downloader.plugins.searching import register_searcher
from novel_downloader.plugins.sites.mangg_net.searcher import ManggNetSearcher


@register_searcher()
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
