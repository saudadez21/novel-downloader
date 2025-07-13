#!/usr/bin/env python3
"""
novel_downloader.core.exporters.esjzone
---------------------------------------

"""

from novel_downloader.core.exporters.registry import register_exporter
from novel_downloader.models import ExporterConfig

from .common import CommonExporter


@register_exporter(site_keys=["esjzone"])
class EsjzoneExporter(CommonExporter):
    def __init__(
        self,
        config: ExporterConfig,
    ):
        super().__init__(
            config,
            site="esjzone",
            chap_folders=["chapters"],
        )


__all__ = ["EsjzoneExporter"]
