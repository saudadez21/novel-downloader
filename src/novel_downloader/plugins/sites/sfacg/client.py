#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.sfacg.client
-------------------------------------------
"""

from novel_downloader.plugins.common.client import CommonClient
from novel_downloader.plugins.registry import registrar


@registrar.register_client()
class SfacgClient(CommonClient):
    """
    Specialized client for SF 轻小说 novel sites.
    """

    @property
    def workers(self) -> int:
        return 1

    def _dl_check_restricted(self, raw_pages: list[str]) -> bool:
        return bool(raw_pages and "本章为VIP章节" in raw_pages[0])

    def _dl_check_empty(self, raw_pages: list[str]) -> bool:
        return bool(raw_pages and "/ajax/ashx/common.ashx" in raw_pages[0])
