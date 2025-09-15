#!/usr/bin/env python3
"""
novel_downloader.core.searchers.ktshu
-------------------------------------

"""

from novel_downloader.core.searchers.mangg_net import ManggNetSearcher
from novel_downloader.core.searchers.registry import register_searcher


@register_searcher(
    site_keys=["ktshu"],
)
class KtshuSearcher(ManggNetSearcher):
    site_name = "ktshu"
    priority = 30
    BASE_URL = "https://www.ktshu.cc"
    SEARCH_URL = "https://www.ktshu.cc/search.php"

    @staticmethod
    def _url_to_id(url: str) -> str:
        # "/book/62773/" -> "62773"
        return url.strip("/").rsplit("/", 1)[-1]
