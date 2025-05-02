#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.parsers.qidian_parser.browser.chapter_encrypted
---------------------------------------------------------------------

"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict

from bs4 import BeautifulSoup

from ..shared import (
    extract_chapter_info,
    find_ssr_page_context,
)

if TYPE_CHECKING:
    from .main_parser import QidianBrowserParser

logger = logging.getLogger(__name__)


def parse_encrypted_chapter(
    parser: QidianBrowserParser,
    soup: BeautifulSoup,
    chapter_id: str,
) -> Dict[str, Any]:
    """
    Extract and return the formatted textual content of an encrypted chapter.

    Steps:
    1. Load SSR JSON context for CSS, fonts, and metadata.
    3. Decode and save randomFont bytes; download fixedFont via download_font().
    4. Extract paragraph structures and save debug JSON.
    5. Parse CSS rules and save debug JSON.
    6. Determine paragraph name prefixes and ending number; save debug text.
    7. Render encrypted paragraphs, then run OCR font‑mapping.
    8. Extracts paragraph texts and formats them.

    :param html_str: Raw HTML content of the chapter page.
    :return: Formatted chapter text or empty string if not parsable.
    """
    try:
        ssr_data = find_ssr_page_context(soup)
        chapter_info = extract_chapter_info(ssr_data)
        if not chapter_info:
            logger.warning(
                "[Parser] ssr_chapterInfo not found for chapter '%s'", chapter_id
            )
            return {}
        return {}
    except Exception as e:
        logger.warning(
            "[Parser] parse error for encrypted chapter '%s': %s", chapter_id, e
        )
        return {}
