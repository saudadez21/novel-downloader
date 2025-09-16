#!/usr/bin/env python3
"""
novel_downloader.utils.text_utils
---------------------------------

Utility modules for text formatting, cleaning, and diff display.
"""

__all__ = [
    "get_cleaner",
    "truncate_half_lines",
]

from .text_cleaner import get_cleaner
from .truncate_utils import truncate_half_lines
