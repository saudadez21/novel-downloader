#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.esjzone
-----------------------------------------

"""

from novel_downloader.core.downloaders.common import CommonDownloader
from novel_downloader.core.interfaces import (
    ExporterProtocol,
    FetcherProtocol,
    ParserProtocol,
)
from novel_downloader.models import DownloaderConfig


class EsjzoneDownloader(CommonDownloader):
    """"""

    def __init__(
        self,
        fetcher: FetcherProtocol,
        parser: ParserProtocol,
        exporter: ExporterProtocol,
        config: DownloaderConfig,
    ):
        super().__init__(fetcher, parser, exporter, config, "esjzone")
