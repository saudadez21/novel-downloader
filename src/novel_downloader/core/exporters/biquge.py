#!/usr/bin/env python3
"""
novel_downloader.core.exporters.biquge
--------------------------------------

"""

__all__ = ["BiqugeExporter"]

from novel_downloader.core.exporters.registry import register_exporter
from novel_downloader.models import ExporterConfig

from .common import CommonExporter


@register_exporter(site_keys=["biquge", "bqg"])
class BiqugeExporter(CommonExporter):
    def __init__(
        self,
        config: ExporterConfig,
    ):
        super().__init__(config, site="biquge")
