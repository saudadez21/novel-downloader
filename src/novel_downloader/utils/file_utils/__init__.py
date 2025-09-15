#!/usr/bin/env python3
"""
novel_downloader.utils.file_utils
---------------------------------

High-level file I/O utility re-exports for convenience.
"""

__all__ = [
    "sanitize_filename",
    "write_file",
]

from .io import write_file
from .sanitize import sanitize_filename
