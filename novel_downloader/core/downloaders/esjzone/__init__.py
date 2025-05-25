#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.esjzone
-----------------------------------------

"""

from .esjzone_async import EsjzoneAsyncDownloader
from .esjzone_sync import EsjzoneDownloader

__all__ = [
    "EsjzoneAsyncDownloader",
    "EsjzoneDownloader",
]
