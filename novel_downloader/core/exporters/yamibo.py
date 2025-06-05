#!/usr/bin/env python3
"""
novel_downloader.core.exporters.yamibo
--------------------------------------

"""

from novel_downloader.models import ExporterConfig

from .common import CommonExporter


class YamiboExporter(CommonExporter):
    def __init__(
        self,
        config: ExporterConfig,
    ):
        super().__init__(
            config,
            site="yamibo",
            chap_folders=["chapters"],
        )


__all__ = ["YamiboExporter"]
