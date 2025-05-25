#!/usr/bin/env python3
"""
novel_downloader.core.savers.yamibo
-----------------------------------

"""

from novel_downloader.config.models import SaverConfig

from .common import CommonSaver


class YamiboSaver(CommonSaver):
    def __init__(
        self,
        config: SaverConfig,
    ):
        super().__init__(
            config,
            site="yamibo",
            chap_folders=["chapters"],
        )


__all__ = ["YamiboSaver"]
