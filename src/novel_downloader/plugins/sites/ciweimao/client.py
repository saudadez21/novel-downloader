#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.ciweimao.client
----------------------------------------------
"""

from novel_downloader.plugins.common.client import CommonClient
from novel_downloader.plugins.registry import registrar


@registrar.register_client()
class CiweimaoClient(CommonClient):
    """
    Specialized client for ciweimao novel sites.
    """

    @property
    def workers(self) -> int:
        return 1
