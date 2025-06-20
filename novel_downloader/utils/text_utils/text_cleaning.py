#!/usr/bin/env python3
"""
novel_downloader.utils.text_utils.text_cleaning
-----------------------------------------------

Tools for detecting and removing promotional or ad-like content from text.
"""

import math
import re

from novel_downloader.utils.file_utils.io import load_blacklisted_words

# --- Constants & Precompiled Patterns ---

_BLACKLISTED_WORDS = load_blacklisted_words()

_BRACKET_PATTERN = re.compile(r"[\(（](.*?)[\)）]")
_K_PROMO_PATTERN = re.compile(r"\b\d{1,4}k\b", re.IGNORECASE)


def clean_chapter_title(title: str) -> str:
    """
    Remove bracketed promotional content from a chapter title.

    If any blacklisted word appears inside parentheses (Chinese or English),
    the entire bracketed section is stripped.

    :param title: Original title, possibly containing ad text in brackets.
    :return:      Title with offending bracketed sections removed.
    """
    cleaned = title
    for content in _BRACKET_PATTERN.findall(title):
        if any(bw in content for bw in _BLACKLISTED_WORDS):
            cleaned = re.sub(rf"[\(（]{re.escape(content)}[\)）]", "", cleaned)
    return cleaned.strip()


def is_promotional_line(line: str) -> bool:
    """
    Check if a line of text likely contains promotional or ad-like content.

    :param line: A single line of text.
    :return:     True if it contains promo keywords or a '###k' vote count pattern.
    """
    low = line.lower()
    if any(kw in low for kw in _BLACKLISTED_WORDS):
        return True
    if _K_PROMO_PATTERN.search(low):
        return True
    return False


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


__all__ = [
    "clean_chapter_title",
    "is_promotional_line",
    "content_prefix",
    "truncate_half_lines",
]
