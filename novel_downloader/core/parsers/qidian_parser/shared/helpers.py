#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.parsers.qidian_parser.shared.helpers
----------------------------------------------------------

Shared utility functions for parsing Qidian browser-rendered pages.

This module provides reusable helpers to:
- Convert HTML into BeautifulSoup objects with fallback.
- Extract SSR-rendered JSON page context and structured chapter metadata.
- Identify VIP chapters, encrypted content, and viewability conditions.
"""

import json
import logging
from typing import Any, Dict, Union

from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


def html_to_soup(html_str: str) -> BeautifulSoup:
    """
    Convert an HTML string to a BeautifulSoup object with fallback.

    :param html_str: Raw HTML string.
    :return: Parsed BeautifulSoup object.
    """
    try:
        return BeautifulSoup(html_str, "lxml")
    except Exception as e:
        logger.warning("[Parser] lxml parse failed, falling back: %s", e)
        return BeautifulSoup(html_str, "html.parser")


def is_vip(html_str: str) -> bool:
    """
    Return True if page indicates VIP‐only content.

    :param html_str: Raw HTML string.
    """
    markers = ["这是VIP章节", "需要订阅", "订阅后才能阅读"]
    return any(m in html_str for m in markers)


def vip_status(soup: BeautifulSoup) -> bool:
    """
    :param soup: Parsed BeautifulSoup object of the HTML page.
    :return: True if VIP, False otherwise.
    """
    ssr_data = find_ssr_page_context(soup)
    chapter_info = extract_chapter_info(ssr_data)
    vip_flag = chapter_info.get("vipStatus", 0)
    fens_flag = chapter_info.get("fEnS", 0)
    return bool(vip_flag == 1 and fens_flag != 0)


def can_view_chapter(soup: BeautifulSoup) -> bool:
    """
    Return True if the chapter is viewable by the current user.

    A chapter is not viewable if it is marked as VIP
    and has not been purchased.

    :param soup: Parsed BeautifulSoup object of the HTML page.
    :return: True if viewable, False otherwise.
    """
    ssr_data = find_ssr_page_context(soup)
    chapter_info = extract_chapter_info(ssr_data)

    is_buy = chapter_info.get("isBuy", 0)
    vip_status = chapter_info.get("vipStatus", 0)

    return not (vip_status == 1 and is_buy == 0)


def is_encrypted(content: Union[str, BeautifulSoup]) -> bool:
    """
    Return True if content is encrypted.

    Chapter Encryption Status (cES):
    - 0: 内容是'明文'
    - 2: 字体加密

    :param content: HTML content, either as a raw string or a BeautifulSoup object.
    :return: True if encrypted marker is found, else False.
    """
    # main = soup.select_one("div#app div#reader-content main")
    # return bool(main and "r-font-encrypt" in main.get("class", []))
    # Normalize to BeautifulSoup
    soup = html_to_soup(content) if isinstance(content, str) else content

    ssr_data = find_ssr_page_context(soup)
    chapter_info = extract_chapter_info(ssr_data)
    return int(chapter_info.get("cES", 0)) == 2


def find_ssr_page_context(soup: BeautifulSoup) -> Dict[str, Any]:
    """
    Extract SSR JSON from <script id="vite-plugin-ssr_pageContext">.
    """
    try:
        tag = soup.find("script", id="vite-plugin-ssr_pageContext")
        if tag and tag.string:
            data: Dict[str, Any] = json.loads(tag.string.strip())
            return data
    except Exception as e:
        logger.warning("[Parser] SSR JSON parse error: %s", e)
    return {}


def extract_chapter_info(ssr_data: Dict[str, Any]) -> Dict[str, Any]:
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
    except Exception as e:
        logger.warning("[Parser] Failed to extract chapterInfo: %s", e)
        return {}
