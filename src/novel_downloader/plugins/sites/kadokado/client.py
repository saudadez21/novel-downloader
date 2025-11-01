#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.kadokado.client
----------------------------------------------
"""

from novel_downloader.plugins.common.client import CommonClient
from novel_downloader.plugins.registry import registrar


@registrar.register_client()
class KadokadoClient(CommonClient):
    """
    Specialized client for kadokado novel sites.
    """

    def _is_access_limited(self, html_list: list[str]) -> bool:
        if len(html_list) < 2:
            return False
        limited_flags = {"NOT_LOGIN", "NOT_SUBSCRIBED", "NOT_PURCHASED"}
        return any(f'"{flag}"' in html_list[1] for flag in limited_flags)
