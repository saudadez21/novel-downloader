#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.savers.epub_utils.text_to_html

Module for converting raw chapter text to formatted HTML,
with automatic word correction and optional image/tag support.
"""

import json
import logging

from novel_downloader.utils.constants import REPLACE_WORD_MAP_PATH
from novel_downloader.utils.text_utils import diff_inline_display

logger = logging.getLogger(__name__)


# Load and sort replacement map from JSON
try:
    replace_map_raw = REPLACE_WORD_MAP_PATH.read_text(encoding="utf-8")
    REPLACE_WORDS_MAP = json.loads(replace_map_raw)
    REPLACE_WORDS_MAP = dict(
        sorted(REPLACE_WORDS_MAP.items(), key=lambda x: len(x[0]), reverse=True)
    )
except Exception as e:
    REPLACE_WORDS_MAP = {}
    logger.info(
        f"[epub] Failed to load REPLACE_WORDS_MAP from {REPLACE_WORD_MAP_PATH}: {e}"
    )


def _check_and_correct_words(txt_str: str) -> str:
    """
    Perform word replacement using REPLACE_WORDS_MAP.

    :param txt_str: Raw string of text.
    :return: String with corrected words.
    """
    for k, v in REPLACE_WORDS_MAP.items():
        txt_str = txt_str.replace(k, v)
    return txt_str


def chapter_txt_to_html(txt_str: str, chapter_title: str) -> str:
    """
    Convert chapter text to styled HTML content.

    :param txt_str: Raw chapter content.
    :param chapter_title: Title of the chapter.
    :return: HTML string including title and paragraphs.
    """
    lines = txt_str.strip().split("\n")
    lines = [line.strip() for line in lines if line.strip()]

    # Remove repeated title from text lines
    if lines and lines[0] == chapter_title.strip():
        lines = lines[1:]

    html_parts = [f"<h2>{chapter_title}</h2>"]

    for line in lines:
        if line.startswith("<img") and line.endswith("/>"):
            html_parts.append(line)
        elif line.startswith(
            '<div class="duokan-image-single illus">'
        ) and line.endswith("</div>"):
            html_parts.append(line)
        elif line == "---":
            html_parts.append("<hr />")
        else:
            corrected_line = _check_and_correct_words(line)
            if corrected_line != line:
                diff = diff_inline_display(line, corrected_line)
                logger.info(f"[epub] Correction diff:\n{diff}")
            html_parts.append(f"<p>{corrected_line}</p>")

    return "\n".join(html_parts)
