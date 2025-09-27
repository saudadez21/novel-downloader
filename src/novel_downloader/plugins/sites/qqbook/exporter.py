#!/usr/bin/env python3
"""
novel_downloader.plugins.sites.qqbook.exporter
----------------------------------------------

Exporter implementation for QQ book novels, supporting plain and encrypted sources.
"""

__all__ = ["QqbookExporter"]

from typing import ClassVar

from novel_downloader.plugins.common.exporter import CommonExporter
from novel_downloader.plugins.registry import registrar


@registrar.register_exporter()
class QqbookExporter(CommonExporter):
    """
    Exporter for QQ 阅读 novels.
    """

    DEFAULT_SOURCE_ID: ClassVar[int] = 0
    ENCRYPTED_SOURCE_ID: ClassVar[int] = 1
    PRIORITIES_MAP: ClassVar[dict[int, int]] = {
        DEFAULT_SOURCE_ID: 0,
        ENCRYPTED_SOURCE_ID: 1,
    }
