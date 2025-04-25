#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.downloaders
---------------------------------

This subpackage contains concrete downloader implementations for
specific novel platforms.

Each downloader is responsible for orchestrating the full lifecycle
of retrieving, parsing, and saving novel content for a given source.
"""

from .common_downloader import CommonDownloader
from .qidian_downloader import QidianDownloader

__all__ = [
    "CommonDownloader",
    "QidianDownloader",
]
