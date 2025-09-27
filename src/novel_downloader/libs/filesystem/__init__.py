#!/usr/bin/env python3
"""
novel_downloader.libs.filesystem
--------------------------------

Filesystem utilities, including file I/O and filename sanitization.
"""

__all__ = [
    "sanitize_filename",
    "write_file",
]

from .file import write_file
from .sanitize import sanitize_filename
