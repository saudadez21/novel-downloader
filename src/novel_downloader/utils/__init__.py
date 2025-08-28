#!/usr/bin/env python3
"""
novel_downloader.utils
----------------------

A collection of helper functions and classes.
"""

__all__ = [
    "ChapterStorage",
    "TextCleaner",
    "parse_cookies",
    "get_cookie_value",
    "rc4_crypt",
    "sanitize_filename",
    "write_file",
    "download",
    "get_cleaner",
    "content_prefix",
    "truncate_half_lines",
    "diff_inline_display",
    "time_diff",
    "async_jitter_sleep",
    "jitter_sleep",
]

from .chapter_storage import ChapterStorage
from .cookies import (
    get_cookie_value,
    parse_cookies,
)
from .crypto_utils import rc4_crypt
from .file_utils import (
    sanitize_filename,
    write_file,
)
from .network import download
from .text_utils import (
    TextCleaner,
    content_prefix,
    diff_inline_display,
    get_cleaner,
    truncate_half_lines,
)
from .time_utils import (
    async_jitter_sleep,
    jitter_sleep,
    time_diff,
)
