#!/usr/bin/env python3
"""
novel_downloader.cli.commands
-----------------------------

"""

__all__ = ["commands"]

from .download import DownloadCmd

commands = [DownloadCmd]
