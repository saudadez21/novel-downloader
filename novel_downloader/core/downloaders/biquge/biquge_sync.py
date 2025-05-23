#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.biquge.biquge_sync
----------------------------------------------------

"""

from novel_downloader.config.models import DownloaderConfig
from novel_downloader.core.downloaders.common import CommonDownloader
from novel_downloader.core.interfaces.parser import ParserProtocol
from novel_downloader.core.interfaces.saver import SaverProtocol
from novel_downloader.core.interfaces.sync_requester import SyncRequesterProtocol


class BiqugeDownloader(CommonDownloader):
    """"""

    def __init__(
        self,
        requester: SyncRequesterProtocol,
        parser: ParserProtocol,
        saver: SaverProtocol,
        config: DownloaderConfig,
    ):
        super().__init__(requester, parser, saver, config, "biquge")
