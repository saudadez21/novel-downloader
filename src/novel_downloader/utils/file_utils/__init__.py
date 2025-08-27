#!/usr/bin/env python3
"""
novel_downloader.utils.file_utils
---------------------------------

High-level file I/O utility re-exports for convenience.
"""

__all__ = [
    "sanitize_filename",
    "save_as_json",
    "save_as_txt",
    "read_text_file",
    "read_json_file",
    "read_binary_file",
    "normalize_txt_line_endings",
]

from .io import (
    read_binary_file,
    read_json_file,
    read_text_file,
    save_as_json,
    save_as_txt,
)
from .normalize import normalize_txt_line_endings
from .sanitize import sanitize_filename
