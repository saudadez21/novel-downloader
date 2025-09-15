#!/usr/bin/env python3
"""
novel_downloader.core.searchers.ciluke
--------------------------------------

"""

from novel_downloader.core.searchers.mangg_net import ManggNetSearcher
from novel_downloader.core.searchers.registry import register_searcher


@register_searcher(
    site_keys=["ciluke"],
)
class CilukeSearcher(ManggNetSearcher):
    site_name = "ciluke"
    priority = 30
    BASE_URL = "https://www.ciluke.com/"
    SEARCH_URL = "https://www.ciluke.com/search.php"

    @staticmethod
    def _url_to_id(url: str) -> str:
        # "/54/54978/" -> "54-54978"
        return url.strip("/").replace("/", "-")
