#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.qqbook.client
--------------------------------------------
"""

from novel_downloader.plugins.common.client import CommonClient
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import ChapterDict


@registrar.register_client()
class QqbookClient(CommonClient):
    """
    Specialized client for QQ 阅读 novel sites.
    """

    @property
    def workers(self) -> int:
        return 1

    def _need_refetch(self, chap: ChapterDict) -> bool:
        """
        Return True if the chapter is marked as font-encrypted
        and should be upserted with need_refetch=True.
        """
        return bool(chap.get("extra", {}).get("font_encrypt", False))
