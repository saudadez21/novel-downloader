#!/usr/bin/env python3
"""
novel_downloader.core.savers.sfacg
----------------------------------

"""

from novel_downloader.config.models import SaverConfig

from .common import CommonSaver


class SfacgSaver(CommonSaver):
    def __init__(
        self,
        config: SaverConfig,
    ):
        super().__init__(
            config,
            site="sfacg",
            chap_folders=["chapters"],
        )


__all__ = ["SfacgSaver"]
