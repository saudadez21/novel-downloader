#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.biquge
----------------------------------------

"""

from novel_downloader.core.downloaders.common import CommonDownloader
from novel_downloader.core.downloaders.registry import register_downloader
from novel_downloader.core.interfaces import (
    FetcherProtocol,
    ParserProtocol,
)
from novel_downloader.models import DownloaderConfig


@register_downloader(site_keys=["biquge", "bqg"])
class BiqugeDownloader(CommonDownloader):
    """
    Downloader for biquge (笔趣阁) novels.
    """

    def __init__(
        self,
        fetcher: FetcherProtocol,
        parser: ParserProtocol,
        config: DownloaderConfig,
    ):
        super().__init__(fetcher, parser, config, "biquge")
