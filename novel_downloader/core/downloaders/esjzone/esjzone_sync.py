#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.esjzone.esjzone_sync
------------------------------------------------------

"""

from novel_downloader.config.models import DownloaderConfig
from novel_downloader.core.downloaders.common import CommonDownloader
from novel_downloader.core.interfaces import (
    ParserProtocol,
    SaverProtocol,
    SyncRequesterProtocol,
)


class EsjzoneDownloader(CommonDownloader):
    """"""

    def __init__(
        self,
        requester: SyncRequesterProtocol,
        parser: ParserProtocol,
        saver: SaverProtocol,
        config: DownloaderConfig,
    ):
        super().__init__(requester, parser, saver, config, "esjzone")
