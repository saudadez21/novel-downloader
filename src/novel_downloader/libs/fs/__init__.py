#!/usr/bin/env python3
"""
novel_downloader.libs.fs
------------------------

High-level file I/O utility re-exports for convenience.
"""

__all__ = [
    "sanitize_filename",
    "write_file",
]

from .file import write_file
from .sanitize import sanitize_filename
