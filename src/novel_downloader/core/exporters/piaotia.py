#!/usr/bin/env python3
"""
novel_downloader.core.exporters.piaotia
---------------------------------------

"""

__all__ = ["PiaotiaExporter"]

from novel_downloader.core.exporters.registry import register_exporter
from novel_downloader.models import ExporterConfig

from .common import CommonExporter


@register_exporter(site_keys=["piaotia"])
class PiaotiaExporter(CommonExporter):
    def __init__(
        self,
        config: ExporterConfig,
    ):
        super().__init__(config, site="piaotia")

    @staticmethod
    def _normalize_book_id(book_id: str) -> str:
        return book_id.replace("/", "-")
