#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.fsshu.searcher
---------------------------------------------

"""

from novel_downloader.plugins.searching import register_searcher
from novel_downloader.plugins.sites.mangg_net.searcher import ManggNetSearcher


@register_searcher()
class FsshuSearcher(ManggNetSearcher):
    site_name = "fsshu"
    priority = 30
    BASE_URL = "https://www.fsshu.com/"
    SEARCH_URL = "https://www.fsshu.com/search.php"

    @staticmethod
    def _url_to_id(url: str) -> str:
        # "/biquge/95_95624/" -> "95_95624"
        return url.strip("/").split("/")[-1]
