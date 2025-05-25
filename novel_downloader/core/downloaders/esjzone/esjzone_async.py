#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.esjzone.esjzone_async
-------------------------------------------------------

"""

from novel_downloader.config.models import DownloaderConfig
from novel_downloader.core.downloaders.common import CommonAsyncDownloader
from novel_downloader.core.interfaces import (
    AsyncRequesterProtocol,
    ParserProtocol,
    SaverProtocol,
)


class EsjzoneAsyncDownloader(CommonAsyncDownloader):
    """"""

    def __init__(
        self,
        requester: AsyncRequesterProtocol,
        parser: ParserProtocol,
        saver: SaverProtocol,
        config: DownloaderConfig,
    ):
        super().__init__(requester, parser, saver, config, "esjzone")
