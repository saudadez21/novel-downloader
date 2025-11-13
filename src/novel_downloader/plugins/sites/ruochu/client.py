#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ruochu.client
--------------------------------------------
"""

from novel_downloader.plugins.common.client import CommonClient
from novel_downloader.plugins.registry import registrar


@registrar.register_client()
class RuochuClient(CommonClient):
    """
    Specialized client for ruochu novel sites.
    """

    def _dl_check_restricted(self, raw_pages: list[str]) -> bool:
        return '"chapter"' not in raw_pages[0]
