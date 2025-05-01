#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.parsers.qidian_parser.session.chapter_normal
------------------------------------------------------------------

Provides `parse_normal_chapter`, which will:

  1. Extract SSR context from a “normal” (non-VIP) chapter page and format it.
  2. Detect VIP/encrypted chapters and fall back to Node-based decryption
     via `QidianNodeDecryptor`.
"""

import logging
from typing import Optional

from bs4 import BeautifulSoup

from novel_downloader.utils.text_utils import format_chapter

from ..shared import (
    extract_chapter_info,
    find_ssr_page_context,
    html_to_soup,
    vip_status,
)
from .node_decryptor import QidianNodeDecryptor

logger = logging.getLogger(__name__)
_decryptor: Optional[QidianNodeDecryptor] = None


def _get_decryptor() -> QidianNodeDecryptor:
    """
    Return the singleton QidianNodeDecryptor, initializing it on first use.
    """
    global _decryptor
    if _decryptor is None:
        _decryptor = QidianNodeDecryptor()
    return _decryptor


def parse_normal_chapter(
    soup: BeautifulSoup,
    chapter_id: str,
    fuid: str,
) -> str:
    """
    Extract and format the chapter text from a normal Qidian page.
    Returns empty string if VIP/encrypted.

    :param soup:      A BeautifulSoup of the chapter HTML.
    :param chapter_id: Chapter identifier (string).
    :param fuid:      Fock user ID parameter from the page.
    :return:          Formatted chapter text, or empty string on error.
    """
    try:
        ssr_data = find_ssr_page_context(soup)
        chapter_info = extract_chapter_info(ssr_data)
        if not chapter_info:
            logger.warning(
                "[Parser] ssr_chapterInfo not found for chapter '%s'", chapter_id
            )
            return ""

        title = chapter_info.get("chapterName", "Untitled")
        raw_html = chapter_info.get("content", "")
        # chapter_id = chapter_info.get("chapterId", "")
        fkp = chapter_info.get("fkp", "")
        author_say = chapter_info.get("authorSay", "")

        if not raw_html:
            return ""

        if vip_status(soup):
            try:
                decryptor = _get_decryptor()
                raw_html = decryptor.decrypt(
                    raw_html,
                    chapter_id,
                    fkp,
                    fuid,
                )
            except Exception as e:
                logger.error("[Parser] decryption failed for '%s': %s", chapter_id, e)
                return ""

        paras_soup = html_to_soup(raw_html)
        paras = [p.get_text(strip=True) for p in paras_soup.find_all("p")]
        chapter_text = "\n\n".join(paras)

        return format_chapter(title, chapter_text, author_say)

    except Exception as e:
        logger.warning(
            "[Parser] parse error for normal chapter '%s': %s", chapter_id, e
        )
        return ""
