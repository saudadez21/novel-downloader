#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.parsers.qidian_parser.browser.chapter_normal
------------------------------------------------------------------

Parser logic for extracting readable text from Qidian chapters
that use plain (non-encrypted) browser-rendered HTML.
"""

import logging
from typing import Any, Dict

from bs4 import BeautifulSoup

from ..shared import (
    extract_chapter_info,
    find_ssr_page_context,
)

logger = logging.getLogger(__name__)


def parse_normal_chapter(
    soup: BeautifulSoup,
    chapter_id: str,
) -> Dict[str, Any]:
    """
    Extract and format the chapter text from a normal Qidian page.
    Returns empty string if VIP/encrypted.

    This method performs the following steps:
      1. Parses HTML into soup.
      2. Skips parsing if VIP or encrypted.
      3. Locates main content container.
      4. Extracts SSR-rendered chapter info (title, author note).
      5. Removes review spans.
      6. Extracts paragraph texts and formats them.

    :param html_str: Raw HTML content of the chapter page.
    :return: Formatted chapter text or empty string if not parsable.
    """
    try:
        main = soup.select_one("div#app div#reader-content main")
        if not main:
            logger.warning("[Parser] Main content not found for chapter")
            return {}

        ssr_data = find_ssr_page_context(soup)
        chapter_info = extract_chapter_info(ssr_data)
        if not chapter_info:
            logger.warning(
                "[Parser] ssr_chapterInfo not found for chapter '%s'", chapter_id
            )
            return {}

        title = chapter_info.get("chapterName", "Untitled")
        chapter_id = chapter_info.get("chapterId", "")
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

        # remove review spans
        for span in main.select("span.review"):
            span.decompose()

        paras = [p.get_text(strip=True) for p in main.find_all("p")]
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
