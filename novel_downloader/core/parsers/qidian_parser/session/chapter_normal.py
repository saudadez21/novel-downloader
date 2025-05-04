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
from typing import Any, Dict, Optional

from bs4 import BeautifulSoup

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
) -> Dict[str, Any]:
    """
    Extract structured chapter info from a normal Qidian page.

    :param soup:      A BeautifulSoup of the chapter HTML.
    :param chapter_id: Chapter identifier (string).
    :param fuid:      Fock user ID parameter from the page.
    :return: a dictionary with keys like 'id', 'title', 'content', etc.
    """
    try:
        ssr_data = find_ssr_page_context(soup)
        chapter_info = extract_chapter_info(ssr_data)
        if not chapter_info:
            logger.warning(
                "[Parser] ssr_chapterInfo not found for chapter '%s'", chapter_id
            )
            return {}

        title = chapter_info.get("chapterName", "Untitled")
        raw_html = chapter_info.get("content", "")
        chapter_id = chapter_info.get("chapterId", "")
        fkp = chapter_info.get("fkp", "")
        author_say = chapter_info.get("authorSay", "")
        update_time = chapter_info.get("updateTime", "")
        update_timestamp = chapter_info.get("updateTimestamp", 0)
        modify_time = chapter_info.get("modifyTime", 0)
        word_count = chapter_info.get("wordsCount", 0)
        vip = bool(chapter_info.get("vipStatus", 0))
        is_buy = bool(chapter_info.get("isBuy", 0))
        seq = chapter_info.get("seq", None)
        order = chapter_info.get("chapterOrder", None)
        volume = chapter_info.get("extra", {}).get("volumeName", "")

        if not raw_html:
            logger.warning("[Parser] raw_html not found for chapter '%s'", chapter_id)
            return {}

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
                return {}

        paras_soup = html_to_soup(raw_html)
        paras = [p.get_text(strip=True) for p in paras_soup.find_all("p")]
        chapter_text = "\n\n".join(paras)

        return {
            "id": str(chapter_id),
            "title": title,
            "content": chapter_text,
            "author_say": author_say.strip() if author_say else "",
            "updated_at": update_time,
            "update_timestamp": update_timestamp,
            "modify_time": modify_time,
            "word_count": word_count,
            "vip": vip,
            "purchased": is_buy,
            "order": order,
            "seq": seq,
            "volume": volume,
        }

    except Exception as e:
        logger.warning(
            "[Parser] parse error for normal chapter '%s': %s", chapter_id, e
        )
        return {}
