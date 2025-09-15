#!/usr/bin/env python3
"""
novel_downloader.core.searchers.xshbook
---------------------------------------

"""

from novel_downloader.core.searchers.registry import register_searcher
from novel_downloader.core.searchers.sososhu import SososhuSearcher


@register_searcher(
    site_keys=["xshbook"],
)
class XshbookSearcher(SososhuSearcher):
    site_name = "xshbook"
    SOSOSHU_KEY = "xshbook"
    BASE_URL = "https://www.xshbook.com"

    @staticmethod
    def _url_to_id(url: str) -> str:
        tail = url.split("xshbook.com", 1)[-1].strip("/")
        return tail.replace("/", "-")
