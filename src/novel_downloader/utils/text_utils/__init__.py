#!/usr/bin/env python3
"""
novel_downloader.utils.text_utils
---------------------------------

Utility modules for text formatting, font mapping, cleaning, and diff display.

Submodules:
- font_mapping: Replace obfuscated characters using font maps
- chapter_formatting: Build structured chapter strings from raw content
- text_cleaning: Remove promo text and check for spam lines
- diff_display: Generate inline diffs with aligned character markers
"""

__all__ = [
    "content_prefix",
    "truncate_half_lines",
    "diff_inline_display",
]

from .diff_display import diff_inline_display
from .truncate_utils import (
    content_prefix,
    truncate_half_lines,
)
