#!/usr/bin/env python3
"""
novel_downloader.core.exporters.qianbi
--------------------------------------

"""

__all__ = ["QianbiExporter"]

from novel_downloader.core.exporters.registry import register_exporter
from novel_downloader.models import ExporterConfig

from .common import CommonExporter


@register_exporter(site_keys=["qianbi"])
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
