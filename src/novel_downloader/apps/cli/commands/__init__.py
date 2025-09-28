#!/usr/bin/env python3
"""
novel_downloader.apps.cli.commands
----------------------------------

CLI command definitions. Each file corresponds to a subcommand.
"""

__all__ = ["commands"]

from .clean import CleanCmd
from .config import ConfigCmd
from .download import DownloadCmd
from .export import ExportCmd
from .search import SearchCmd

commands = [CleanCmd, ConfigCmd, DownloadCmd, ExportCmd, SearchCmd]
