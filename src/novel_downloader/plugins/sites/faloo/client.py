#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.faloo.client
-------------------------------------------
"""

from novel_downloader.plugins.common.client import CommonClient
from novel_downloader.plugins.registry import registrar


@registrar.register_client()
class FalooClient(CommonClient):
    """
    Specialized client for faloo novel sites.
    """

    @property
    def workers(self) -> int:
        return 1

    def _dl_check_restricted(self, raw_pages: list[str]) -> bool:
        raw_page = raw_pages[0]
        return (
            "您还没有订阅本章节" in raw_page
            or "您还没有登录，请登录后在继续阅读本部小说" in raw_page
        )
