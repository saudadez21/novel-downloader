#!/usr/bin/env python3
"""
novel_downloader.utils.text_utils
---------------------------------

Utility modules for text formatting, font mapping, cleaning, and diff display.

Submodules:
- diff_display: Generate inline diffs with aligned character markers
- numeric_conversion: Convert between Chinese and Arabic numerals
- text_cleaner: Text cleaning and normalization utilities
- truncate_utils: Text truncation and content prefix generation
"""

__all__ = [
    "TextCleaner",
    "get_cleaner",
    "content_prefix",
    "truncate_half_lines",
    "chinese_to_arabic",
    "arabic_to_chinese",
    "diff_inline_display",
]

from .diff_display import diff_inline_display
from .numeric_conversion import (
    arabic_to_chinese,
    chinese_to_arabic,
)
from .text_cleaner import TextCleaner, get_cleaner
from .truncate_utils import (
    content_prefix,
    truncate_half_lines,
)
