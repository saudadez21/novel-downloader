#!/usr/bin/env python3
"""
novel_downloader.utils
----------------------

"""

__all__ = [
    "ChapterStorage",
    "resolve_cookies",
    "parse_cookie_expires",
    "find_cookie_value",
    "rc4_crypt",
    "sanitize_filename",
    "save_as_json",
    "save_as_txt",
    "read_text_file",
    "read_json_file",
    "read_binary_file",
    "download",
    "content_prefix",
    "truncate_half_lines",
    "diff_inline_display",
    "calculate_time_difference",
    "async_sleep_with_random_delay",
    "sleep_with_random_delay",
]

from .chapter_storage import ChapterStorage
from .cookies import (
    find_cookie_value,
    parse_cookie_expires,
    resolve_cookies,
)
from .crypto_utils import rc4_crypt
from .file_utils import (
    read_binary_file,
    read_json_file,
    read_text_file,
    sanitize_filename,
    save_as_json,
    save_as_txt,
)
from .network import download
from .text_utils import (
    content_prefix,
    diff_inline_display,
    truncate_half_lines,
)
from .time_utils import (
    async_sleep_with_random_delay,
    calculate_time_difference,
    sleep_with_random_delay,
)
