#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.xshbook.searcher
-----------------------------------------------

"""

from novel_downloader.plugins.common.searcher.sososhu import SososhuSearcher
from novel_downloader.plugins.registry import registrar


@registrar.register_searcher()
class XshbookSearcher(SososhuSearcher):
    site_name = "xshbook"
    SOSOSHU_KEY = "xshbook"
    BASE_URL = "https://www.xshbook.com"

    @staticmethod
    def _url_to_id(url: str) -> str:
        tail = url.split("xshbook.com", 1)[-1].strip("/")
        return tail.replace("/", "-")
