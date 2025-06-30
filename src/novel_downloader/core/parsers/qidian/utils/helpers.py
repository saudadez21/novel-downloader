#!/usr/bin/env python3
"""
novel_downloader.core.parsers.qidian.utils.helpers
--------------------------------------------------

Shared utility functions for parsing Qidian pages.

This module provides reusable helpers to:
- Extract SSR-rendered JSON page context and structured chapter metadata.
- Identify VIP chapters, encrypted content, and viewability conditions.
"""

import json
import logging
from typing import Any

from lxml import html

logger = logging.getLogger(__name__)


def find_ssr_page_context(html_str: str) -> dict[str, Any]:
    """
    Extract SSR JSON from <script id="vite-plugin-ssr_pageContext">.
    """
    try:
        tree = html.fromstring(html_str)
        script = tree.xpath('//script[@id="vite-plugin-ssr_pageContext"]/text()')
        if script:
            data: dict[str, Any] = json.loads(script[0].strip())
            return data
    except Exception as e:
        logger.warning("[Parser] SSR JSON parse error: %s", e)
    return {}


def extract_chapter_info(ssr_data: dict[str, Any]) -> dict[str, Any]:
    """
    Extract the 'chapterInfo' dictionary from the SSR page context.

    This handles nested key access and returns an empty dict if missing.

    :param ssr_data: The full SSR data object from _find_ssr_page_context().
    :return: A dict with chapter metadata such as chapterName, authorSay, etc.
    """
    try:
        page_context = ssr_data.get("pageContext", {})
        page_props = page_context.get("pageProps", {})
        page_data = page_props.get("pageData", {})
        chapter_info = page_data.get("chapterInfo", {})

        assert isinstance(chapter_info, dict)
        return chapter_info
    except Exception:
        return {}


def is_restricted_page(html_str: str) -> bool:
    """
    Return True if page content indicates access restriction
    (e.g. not subscribed/purchased).

    :param html_str: Raw HTML string.
    """
    markers = ["这是VIP章节", "需要订阅", "订阅后才能阅读"]
    return any(m in html_str for m in markers)


def vip_status(ssr_data: dict[str, Any]) -> bool:
    """
    :return: True if VIP, False otherwise.
    """
    chapter_info = extract_chapter_info(ssr_data)
    vip_flag = chapter_info.get("vipStatus", 0)
    fens_flag = chapter_info.get("fEnS", 0)
    return bool(vip_flag == 1 and fens_flag != 0)


def can_view_chapter(ssr_data: dict[str, Any]) -> bool:
    """
    A chapter is not viewable if it is marked as VIP
    and has not been purchased.

    :return: True if viewable, False otherwise.
    """
    chapter_info = extract_chapter_info(ssr_data)
    is_buy = chapter_info.get("isBuy", 0)
    vip_status = chapter_info.get("vipStatus", 0)
    return not (vip_status == 1 and is_buy == 0)


def is_duplicated(ssr_data: dict[str, Any]) -> bool:
    """
    Check if chapter is marked as duplicated (eFW = 1).
    """
    chapter_info = extract_chapter_info(ssr_data)
    efw_flag = chapter_info.get("eFW", 0)
    return bool(efw_flag == 1)


def is_encrypted(content: str | dict[str, Any]) -> bool:
    """
    Return True if content is encrypted.

    Chapter Encryption Status (cES):
    - 0: 内容是'明文'
    - 2: 字体加密

    :param content: HTML content, either as a raw string or a BeautifulSoup object.
    :return: True if encrypted marker is found, else False.
    """
    ssr_data = find_ssr_page_context(content) if isinstance(content, str) else content
    chapter_info = extract_chapter_info(ssr_data)
    return int(chapter_info.get("cES", 0)) == 2
