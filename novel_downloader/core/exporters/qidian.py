#!/usr/bin/env python3
"""
novel_downloader.core.exporters.qidian
--------------------------------------

This module provides the `QidianExporter` class for handling the saving process
of novels sourced from Qidian (起点中文网). It implements the platform-specific
logic required to structure and export novel content into desired formats.
"""

from novel_downloader.models import ExporterConfig

from .common import CommonExporter


class QidianExporter(CommonExporter):
    def __init__(
        self,
        config: ExporterConfig,
    ):
        super().__init__(
            config,
            site="qidian",
            chap_folders=["chapters", "encrypted_chapters"],
        )


__all__ = ["QidianExporter"]
