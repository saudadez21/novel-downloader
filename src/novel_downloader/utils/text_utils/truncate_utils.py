#!/usr/bin/env python3
"""
novel_downloader.utils.text_utils.truncate_utils
------------------------------------------------

Tools for truncating text.
"""

__all__ = [
    "content_prefix",
    "truncate_half_lines",
]

import math


def content_prefix(
    text: str,
    n: int,
    ignore_chars: set[str] | None = None,
) -> str:
    """
    Return the prefix of `text` containing the first `n` non-ignored characters.

    :param text: The full input string.
    :param n: Number of content characters to include.
    :param ignore_chars: Characters to ignore when counting content.
    :return: Truncated string preserving original whitespace and line breaks.
    """
    ignore = ignore_chars or set()
    cnt = 0

    for i, ch in enumerate(text):
        if ch not in ignore:
            cnt += 1
            if cnt >= n:
                return text[: i + 1]

    return text


def truncate_half_lines(text: str) -> str:
    """
    Keep the first half of the lines (rounded up), preserving line breaks.

    :param text: Full input text
    :return: Truncated text with first half of lines
    """
    lines = text.splitlines()
    non_empty_lines = [line for line in lines if line.strip()]
    keep_count = math.ceil(len(non_empty_lines) / 2)

    result_lines = []
    count = 0
    for line in lines:
        result_lines.append(line)
        if line.strip():
            count += 1
        if count >= keep_count:
            break

    return "\n".join(result_lines)
