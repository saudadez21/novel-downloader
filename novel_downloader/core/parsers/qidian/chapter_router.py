#!/usr/bin/env python3
"""
novel_downloader.core.parsers.qidian.chapter_router
---------------------------------------------------

Routing logic for selecting the correct chapter parser for Qidian pages.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from novel_downloader.models import ChapterDict

from .chapter_normal import parse_normal_chapter
from .utils import (
    can_view_chapter,
    find_ssr_page_context,
    is_encrypted,
)

if TYPE_CHECKING:
    from .main_parser import QidianParser

logger = logging.getLogger(__name__)


def parse_chapter(
    parser: QidianParser,
    html_str: str,
    chapter_id: str,
) -> ChapterDict | None:
    """
    Extract and return the formatted textual content of chapter.

    :param parser: Instance of QidianParser.
    :param html_str: Raw HTML content of the chapter page.
    :param chapter_id: Identifier of the chapter being parsed.
    :return: Formatted chapter text or empty string if not parsable.
    """
    try:
        ssr_data = find_ssr_page_context(html_str)

        if not can_view_chapter(ssr_data):
            logger.warning(
                "[Parser] Chapter '%s' is not purchased or inaccessible.", chapter_id
            )
            return None

        if is_encrypted(ssr_data):
            if not parser._decode_font:
                return None
            try:
                from .chapter_encrypted import parse_encrypted_chapter

                return parse_encrypted_chapter(parser, html_str, chapter_id)
            except ImportError:
                logger.warning(
                    "[Parser] Encrypted chapter '%s' requires extra dependencies.",
                    chapter_id,
                )
                return None

        return parse_normal_chapter(parser, html_str, chapter_id)
    except Exception as e:
        logger.warning("[Parser] parse error for chapter '%s': %s", chapter_id, e)
    return None
