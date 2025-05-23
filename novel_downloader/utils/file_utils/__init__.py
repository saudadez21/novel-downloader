#!/usr/bin/env python3
"""
novel_downloader.utils.file_utils
---------------------------------

High-level file I/O utility re-exports for convenience.

This module aggregates commonly used low-level file utilities such as:
- Path sanitization (for safe filenames)
- Text normalization (e.g. Windows/Linux line endings)
- JSON, plain text, and binary file reading/writing

Included utilities:
- sanitize_filename: remove invalid characters from filenames
- normalize_txt_line_endings: standardize line endings in text files
- save_as_json / save_as_txt: write dict or text to file
- read_text_file / read_json_file / read_binary_file: load content from file
"""

from .io import (
    load_blacklisted_words,
    load_text_resource,
    read_binary_file,
    read_json_file,
    read_text_file,
    save_as_json,
    save_as_txt,
)
from .normalize import normalize_txt_line_endings
from .sanitize import sanitize_filename

__all__ = [
    "sanitize_filename",
    "save_as_json",
    "save_as_txt",
    "read_text_file",
    "read_json_file",
    "read_binary_file",
    "load_text_resource",
    "load_blacklisted_words",
    "normalize_txt_line_endings",
]
