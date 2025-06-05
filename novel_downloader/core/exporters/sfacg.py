#!/usr/bin/env python3
"""
novel_downloader.core.exporters.sfacg
-------------------------------------

"""

from novel_downloader.models import ExporterConfig

from .common import CommonExporter


class SfacgExporter(CommonExporter):
    def __init__(
        self,
        config: ExporterConfig,
    ):
        super().__init__(
            config,
            site="sfacg",
            chap_folders=["chapters"],
        )


__all__ = ["SfacgExporter"]
