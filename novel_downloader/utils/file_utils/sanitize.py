#!/usr/bin/env python3
"""
novel_downloader.utils.file_utils.sanitize
------------------------------------------

Utility functions for cleaning and validating filenames for safe use
on different operating systems.

This module provides a cross-platform `sanitize_filename` function
that replaces or removes illegal characters from filenames, trims
lengths, and avoids reserved names on Windows systems.
"""

import logging
import os
import re

logger = logging.getLogger(__name__)

# Windows 保留名称列表 (忽略大小写)
_WIN_RESERVED_NAMES = {
    "CON",
    "PRN",
    "AUX",
    "NUL",
    *(f"COM{i}" for i in range(1, 10)),
    *(f"LPT{i}" for i in range(1, 10)),
}

_SANITIZE_PATTERN_WIN = re.compile(r'[<>:"/\\|?*\x00-\x1F]')
_SANITIZE_PATTERN_POSIX = re.compile(r"[/\x00]")


def sanitize_filename(filename: str, max_length: int | None = 255) -> str:
    """
    Sanitize the given filename by replacing characters
    that are invalid in file paths with '_'.

    This function checks the operating system environment and applies the appropriate
    filtering rules:
      - On Windows, it replaces characters: <>:"/\\|?*
      - On POSIX systems, it replaces the forward slash '/'

    :param filename: The input filename to sanitize.
    :param max_length: Optional maximum length of the output filename. Defaults to 255.
    :return: The sanitized filename as a string.
    """
    pattern = _SANITIZE_PATTERN_WIN if os.name == "nt" else _SANITIZE_PATTERN_POSIX

    name = pattern.sub("_", filename).strip(" .")

    stem, dot, ext = name.partition(".")
    if os.name == "nt" and stem.upper() in _WIN_RESERVED_NAMES:
        stem = f"_{stem}"
    cleaned = f"{stem}{dot}{ext}" if ext else stem

    if max_length and len(cleaned) > max_length:
        if ext:
            keep = max_length - len(ext) - 1
            cleaned = f"{cleaned[:keep]}.{ext}"
        else:
            cleaned = cleaned[:max_length]

    if not cleaned:
        cleaned = "_untitled"
    logger.debug("[file] Sanitized filename: %r -> %r", filename, cleaned)
    return cleaned


__all__ = ["sanitize_filename"]
