#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ciluke.searcher
----------------------------------------------

"""

from novel_downloader.plugins.searching import register_searcher
from novel_downloader.plugins.sites.mangg_net.searcher import ManggNetSearcher


@register_searcher()
class CilukeSearcher(ManggNetSearcher):
    site_name = "ciluke"
    priority = 30
    BASE_URL = "https://www.ciluke.com/"
    SEARCH_URL = "https://www.ciluke.com/search.php"

    @staticmethod
    def _url_to_id(url: str) -> str:
        # "/54/54978/" -> "54-54978"
        return url.strip("/").replace("/", "-")
