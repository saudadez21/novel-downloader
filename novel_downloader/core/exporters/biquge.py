#!/usr/bin/env python3
"""
novel_downloader.core.exporters.biquge
--------------------------------------

"""

from novel_downloader.models import ExporterConfig

from .common import CommonExporter


class BiqugeExporter(CommonExporter):
    def __init__(
        self,
        config: ExporterConfig,
    ):
        super().__init__(
            config,
            site="biquge",
            chap_folders=["chapters"],
        )


__all__ = ["BiqugeExporter"]
