#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.shencou.client
---------------------------------------------
"""

from novel_downloader.plugins.common.client import CommonClient
from novel_downloader.plugins.registry import registrar


@registrar.register_client()
class ShencouClient(CommonClient):
    """
    Specialized client for 神凑轻小说文库 novel sites.
    """

    def _is_access_limited(self, html_list: list[str]) -> bool:
        return "404错误，页面不存在，或文章已删除" in html_list[0]
