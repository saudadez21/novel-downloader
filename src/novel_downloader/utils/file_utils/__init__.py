#!/usr/bin/env python3
"""
novel_downloader.utils.file_utils
---------------------------------

High-level file I/O utility re-exports for convenience.
"""

__all__ = [
    "sanitize_filename",
    "write_file",
    "normalize_txt_line_endings",
]

from .io import write_file
from .normalize import normalize_txt_line_endings
from .sanitize import sanitize_filename
