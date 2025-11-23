#!/usr/bin/env python3
"""
novel_downloader.plugins.mixins
-------------------------------
"""

__all__ = [
    "CleanupMixin",
    "DownloadMixin",
    "ExportEpubMixin",
    "ExportHtmlMixin",
    "ExportTxtMixin",
    "ProcessMixin",
]

from .cleanup import CleanupMixin
from .download import DownloadMixin
from .export_epub import ExportEpubMixin
from .export_html import ExportHtmlMixin
from .export_txt import ExportTxtMixin
from .process import ProcessMixin
