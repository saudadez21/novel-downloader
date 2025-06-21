#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.sfacg
---------------------------------------

"""

from novel_downloader.core.downloaders.common import CommonDownloader
from novel_downloader.core.interfaces import (
    FetcherProtocol,
    ParserProtocol,
)
from novel_downloader.models import DownloaderConfig


class SfacgDownloader(CommonDownloader):
    """"""

    def __init__(
        self,
        fetcher: FetcherProtocol,
        parser: ParserProtocol,
        config: DownloaderConfig,
    ):
        super().__init__(fetcher, parser, config, "sfacg")
