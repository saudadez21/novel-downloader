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

    def _is_access_limited(self, html_list: list[str]) -> bool:
        return '"chapter"' not in html_list[0]
