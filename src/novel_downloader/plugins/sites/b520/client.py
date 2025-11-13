#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.b520.client
------------------------------------------
"""

from novel_downloader.plugins.common.client import CommonClient
from novel_downloader.plugins.registry import registrar


@registrar.register_client()
class B520Client(CommonClient):
    """
    Specialized client for b520 novel sites.
    """

    def _dl_check_restricted(self, raw_pages: list[str]) -> bool:
        return "<h1>Bad GateWay</h1>" in raw_pages[0]
