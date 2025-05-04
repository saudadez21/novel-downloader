#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.parsers.qidian_parser.browser.chapter_router
------------------------------------------------------------------

Routing logic for selecting the correct chapter parser for Qidian browser pages.

This module acts as a dispatcher that analyzes a chapter's HTML content and
routes the parsing task to either the encrypted or normal chapter parser.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, Dict

from ..shared import (
    can_view_chapter,
    html_to_soup,
    is_encrypted,
)
from .chapter_normal import parse_normal_chapter

if TYPE_CHECKING:
    from .main_parser import QidianBrowserParser

logger = logging.getLogger(__name__)


def parse_chapter(
    parser: QidianBrowserParser,
    html_str: str,
    chapter_id: str,
) -> Dict[str, Any]:
    """
    Extract and return the formatted textual content of chapter.

    :param parser: Instance of QidianBrowserParser.
    :param html_str: Raw HTML content of the chapter page.
    :param chapter_id: Identifier of the chapter being parsed.
    :return: Formatted chapter text or empty string if not parsable.
    """
    try:
        soup = html_to_soup(html_str)

        if not can_view_chapter(soup):
            logger.warning(
                "[Parser] Chapter '%s' is not purchased or inaccessible.", chapter_id
            )
            return {}

        if is_encrypted(soup):
            if not parser._decode_font:
                return {}
            try:
                from .chapter_encrypted import parse_encrypted_chapter

                return parse_encrypted_chapter(parser, soup, chapter_id)
            except ImportError:
                logger.warning(
                    "[Parser] Encrypted chapter '%s' requires extra dependencies.",
                    chapter_id,
                )
                return {}

        return parse_normal_chapter(soup, chapter_id)
    except Exception as e:
        logger.warning("[Parser] parse error for chapter '%s': %s", chapter_id, e)
        return {}
