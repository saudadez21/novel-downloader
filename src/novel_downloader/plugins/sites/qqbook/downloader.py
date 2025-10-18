#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.qqbook.downloader
------------------------------------------------

Downloader implementation for QQ novels, with unpurchased chapter ID skip logic.
"""


from novel_downloader.plugins.common.downloader import DualBatchDownloader
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import ChapterDict


@registrar.register_downloader()
class QqbookDownloader(DualBatchDownloader):
    """
    Specialized downloader for QQ 阅读 novels.

    Processes each chapter in a single worker that skip non-accessible
    and handles fetch -> parse -> enqueue storage.
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
