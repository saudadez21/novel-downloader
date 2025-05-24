#!/usr/bin/env python3
"""
novel_downloader.core.savers.qianbi
-----------------------------------

"""

from novel_downloader.config.models import SaverConfig

from .common import CommonSaver


class QianbiSaver(CommonSaver):
    def __init__(
        self,
        config: SaverConfig,
    ):
        super().__init__(
            config,
            site="qianbi",
            chap_folders=["chapters"],
        )


__all__ = ["QianbiSaver"]
