#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ciyuanji.client
----------------------------------------------
"""

from novel_downloader.plugins.common.client import CommonClient
from novel_downloader.plugins.registry import registrar


@registrar.register_client()
class CiyuanjiClient(CommonClient):
    """
    Specialized client for 次元姬 novel sites.
    """

    @property
    def workers(self) -> int:
        return 1
