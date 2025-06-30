#!/usr/bin/env python3
"""
novel_downloader.core.exporters.qianbi
--------------------------------------

"""

from novel_downloader.models import ExporterConfig

from .common import CommonExporter


class QianbiExporter(CommonExporter):
    def __init__(
        self,
        config: ExporterConfig,
    ):
        super().__init__(
            config,
            site="qianbi",
            chap_folders=["chapters"],
        )


__all__ = ["QianbiExporter"]
