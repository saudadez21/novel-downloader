#!/usr/bin/env python3
"""
novel_downloader.core.exporters.qidian
--------------------------------------

Exporter implementation for Qidian novels, supporting plain and encrypted sources.
"""

__all__ = ["QidianExporter"]

from novel_downloader.core.exporters.registry import register_exporter
from novel_downloader.models import ExporterConfig

from .common import CommonExporter


@register_exporter(site_keys=["qidian", "qd"])
class QidianExporter(CommonExporter):
    """ """

    DEFAULT_SOURCE_ID = 0
    ENCRYPTED_SOURCE_ID = 1
    PRIORITIES_MAP = {
        DEFAULT_SOURCE_ID: 0,
        ENCRYPTED_SOURCE_ID: 1,
    }

    def __init__(
        self,
        config: ExporterConfig,
    ):
        super().__init__(config, site="qidian")
