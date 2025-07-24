#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.piaotia
-----------------------------------------

"""

from novel_downloader.core.downloaders.common import CommonDownloader
from novel_downloader.core.downloaders.registry import register_downloader
from novel_downloader.core.interfaces import (
    FetcherProtocol,
    ParserProtocol,
)
from novel_downloader.models import DownloaderConfig


@register_downloader(site_keys=["piaotia"])
class PiaotiaDownloader(CommonDownloader):
    """
    Downloader for piaotia (飘天文学网) novels.
    """

    def __init__(
        self,
        fetcher: FetcherProtocol,
        parser: ParserProtocol,
        config: DownloaderConfig,
    ):
        super().__init__(fetcher, parser, config, "piaotia")

    @staticmethod
    def _normalize_book_id(book_id: str) -> str:
        return book_id.replace("/", "-")
