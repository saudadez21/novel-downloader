#!/usr/bin/env python3
"""
novel_downloader.core.searchers.fsshu
-------------------------------------

"""

from novel_downloader.core.searchers.mangg_net import ManggNetSearcher
from novel_downloader.core.searchers.registry import register_searcher


@register_searcher(
    site_keys=["fsshu"],
)
class FsshuSearcher(ManggNetSearcher):
    site_name = "fsshu"
    priority = 30
    BASE_URL = "https://www.fsshu.com/"
    SEARCH_URL = "https://www.fsshu.com/search.php"

    @staticmethod
    def _url_to_id(url: str) -> str:
        # "/biquge/95_95624/" -> "95_95624"
        return url.strip("/").split("/")[-1]
