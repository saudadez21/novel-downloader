#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.n17k.client
------------------------------------------
"""

from novel_downloader.plugins.common.client import CommonClient
from novel_downloader.plugins.registry import registrar


@registrar.register_client()
class N17kClient(CommonClient):
    """
    Specialized client for n17k novel sites.
    """

    def _is_access_limited(self, html_list: list[str]) -> bool:
        return "VIP章节, 余下还有" in html_list[0]
