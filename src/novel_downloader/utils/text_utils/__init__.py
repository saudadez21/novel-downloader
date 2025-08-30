#!/usr/bin/env python3
"""
novel_downloader.utils.text_utils
---------------------------------

Utility modules for text formatting, cleaning, and diff display.
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
