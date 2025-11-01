#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.uaa.client
-----------------------------------------
"""

from novel_downloader.plugins.common.client import CommonClient
from novel_downloader.plugins.registry import registrar


@registrar.register_client()
class UaaClient(CommonClient):
    """
    Specialized client for uaa novel sites.
    """

    def _is_access_limited(self, html_list: list[str]) -> bool:
        return "以下正文内容已隐藏" in html_list[0]
