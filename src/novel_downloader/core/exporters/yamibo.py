#!/usr/bin/env python3
"""
novel_downloader.core.exporters.yamibo
--------------------------------------

"""

__all__ = ["YamiboExporter"]

from novel_downloader.core.exporters.registry import register_exporter
from novel_downloader.models import ExporterConfig

from .common import CommonExporter


@register_exporter(site_keys=["yamibo"])
class YamiboExporter(CommonExporter):
    def __init__(
        self,
        config: ExporterConfig,
    ):
        super().__init__(config, site="yamibo")
