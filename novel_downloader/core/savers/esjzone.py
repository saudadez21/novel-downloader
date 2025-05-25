#!/usr/bin/env python3
"""
novel_downloader.core.savers.esjzone
------------------------------------

"""

from novel_downloader.config.models import SaverConfig

from .common import CommonSaver


class EsjzoneSaver(CommonSaver):
    def __init__(
        self,
        config: SaverConfig,
    ):
        super().__init__(
            config,
            site="esjzone",
            chap_folders=["chapters"],
        )


__all__ = ["EsjzoneSaver"]
