#!/usr/bin/env python3
"""
novel_downloader.core.savers.biquge
-----------------------------------

"""

from novel_downloader.config.models import SaverConfig

from .common import CommonSaver


class BiqugeSaver(CommonSaver):
    def __init__(
        self,
        config: SaverConfig,
    ):
        super().__init__(
            config,
            site="biquge",
            chap_folders=["chapters"],
        )


__all__ = ["BiqugeSaver"]
