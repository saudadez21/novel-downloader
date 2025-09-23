#!/usr/bin/env python3
"""
novel_downloader.cli.commands
-----------------------------

"""

__all__ = ["commands"]

from .download import DownloadCmd
from .export import ExportCmd
from .search import SearchCmd

commands = [DownloadCmd, ExportCmd, SearchCmd]
