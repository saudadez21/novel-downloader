#!/usr/bin/env python3
"""
novel_downloader.core.exporters.xiaoshuowu
------------------------------------------

"""

__all__ = ["XiaoshuowuExporter"]

from novel_downloader.core.exporters.registry import register_exporter
from novel_downloader.models import ExporterConfig

from .common import CommonExporter


@register_exporter(site_keys=["xiaoshuowu"])
class XiaoshuowuExporter(CommonExporter):
    def __init__(
        self,
        config: ExporterConfig,
    ):
        super().__init__(config, site="xiaoshuowu")

    @staticmethod
    def _normalize_book_id(book_id: str) -> str:
        return book_id.replace("/", "-")
