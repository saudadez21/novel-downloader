#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ktshu.searcher
---------------------------------------------

"""

from novel_downloader.plugins.searching import register_searcher
from novel_downloader.plugins.sites.mangg_net.searcher import ManggNetSearcher


@register_searcher()
class KtshuSearcher(ManggNetSearcher):
    site_name = "ktshu"
    priority = 30
    BASE_URL = "https://www.ktshu.cc"
    SEARCH_URL = "https://www.ktshu.cc/search.php"

    @staticmethod
    def _url_to_id(url: str) -> str:
        # "/book/62773/" -> "62773"
        return url.strip("/").rsplit("/", 1)[-1]
