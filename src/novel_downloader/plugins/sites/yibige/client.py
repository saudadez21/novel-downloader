#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.yibige.client
--------------------------------------------
"""

from novel_downloader.plugins.common.client import CommonClient
from novel_downloader.plugins.registry import registrar


@registrar.register_client()
class YibigeClient(CommonClient):
    """
    Specialized client for 一笔阁 novel sites.
    """

    def _is_access_limited(self, html_list: list[str]) -> bool:
        return "<b>Parse error</b>" in html_list[0]
