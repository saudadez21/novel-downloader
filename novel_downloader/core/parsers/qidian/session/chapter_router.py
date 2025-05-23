#!/usr/bin/env python3
"""
novel_downloader.core.parsers.qidian.session.chapter_router
-----------------------------------------------------------

Routing logic for selecting the correct chapter parser for Qidian session pages.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from novel_downloader.utils.chapter_storage import ChapterDict

from ..shared import (
    can_view_chapter,
    html_to_soup,
    is_encrypted,
)
from .chapter_normal import parse_normal_chapter

if TYPE_CHECKING:
    from .main_parser import QidianSessionParser

logger = logging.getLogger(__name__)


def parse_chapter(
    parser: QidianSessionParser,
    html_str: str,
    chapter_id: str,
) -> ChapterDict | None:
    """
    Extract and return the formatted textual content of chapter.

    :param parser: Instance of QidianSessionParser.
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
            return None

        if is_encrypted(soup):
            if not parser._decode_font:
                return None
            try:
                from .chapter_encrypted import parse_encrypted_chapter

                return parse_encrypted_chapter(parser, soup, chapter_id, parser._fuid)
            except ImportError:
                logger.warning(
                    "[Parser] Encrypted chapter '%s' requires extra dependencies.",
                    chapter_id,
                )
                return None

        return parse_normal_chapter(soup, chapter_id, parser._fuid)
    except Exception as e:
        logger.warning("[Parser] parse error for chapter '%s': %s", chapter_id, e)
    return None
