#!/usr/bin/env python3
"""
novel_downloader.plugins.mixins
-------------------------------
"""

__all__ = [
    "DownloadMixin",
    "ExportEpubMixin",
    "ExportHtmlMixin",
    "ExportTxtMixin",
]

from .download import DownloadMixin
from .export_epub import ExportEpubMixin
from .export_html import ExportHtmlMixin
from .export_txt import ExportTxtMixin
