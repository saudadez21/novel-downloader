#!/usr/bin/env python3
"""
novel_downloader.libs.textutils
-------------------------------

Text processing helpers such as number handling, text cleaning, and truncation.
"""

__all__ = [
    "get_cleaner",
    "truncate_half_lines",
]

from .text_cleaner import get_cleaner
from .truncate import truncate_half_lines
