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

from .chapter_formatting import format_chapter
from .diff_display import diff_inline_display
from .font_mapping import apply_font_mapping
from .text_cleaning import (
    clean_chapter_title,
    content_prefix,
    is_promotional_line,
    truncate_half_lines,
)

__all__ = [
    "apply_font_mapping",
    "format_chapter",
    "clean_chapter_title",
    "is_promotional_line",
    "content_prefix",
    "truncate_half_lines",
    "diff_inline_display",
]
