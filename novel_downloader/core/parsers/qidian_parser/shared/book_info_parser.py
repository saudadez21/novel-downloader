#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.parsers.qidian_parser.shared.book_info_parser
-------------------------------------------------------------------

This module provides parsing of Qidian book info pages.

It extracts metadata such as title, author, cover URL, update
time, status, word count, summary, and volume-chapter structure.
"""

import logging
import re
from typing import Any, Dict

from bs4.element import Tag

from .helpers import html_to_soup

logger = logging.getLogger(__name__)


def _chapter_url_to_id(url: str) -> str:
    """
    Extract chapterId as the last non-empty segment of the URL.
    """
    return url.rstrip("/").split("/")[-1]


def _get_volume_name(vol_div: Tag) -> str:
    """
    Extracts the volume title from a <div class="volume"> element
    """
    h3 = vol_div.select_one("h3")
    if not h3:
        return ""
    for a in h3.find_all("a"):
        a.decompose()
    text: str = h3.get_text(strip=True)
    return text.split(chr(183))[0].strip()


def parse_book_info(html_str: str) -> Dict[str, Any]:
    """
    Extract metadata: title, author, cover_url, update_time, status,
    word_count, summary, and volumes with chapters.

    :param html_str: Raw HTML of the book info page.
    :return: A dict containing book metadata.
    """
    info: Dict[str, Any] = {}
    try:
        soup = html_to_soup(html_str)
        info["book_name"] = soup.select_one("em#bookName").get_text(strip=True)
        info["author"] = soup.select_one("a.writer").get_text(strip=True)
        info["cover_url"] = soup.select_one("div.book-img img")["src"].strip()
        info["update_time"] = (
            soup.select_one("span.book-update-time")
            .get_text(strip=True)
            .replace("更新时间", "")
            .strip()
        )
        info["serial_status"] = soup.select_one("span.blue").get_text(strip=True)
        # word count via regex
        match = re.search(
            r"<em>([\d.]+)</em>\s*<cite>(.*?)字</cite>",
            html_str,
        )
        if match:
            info["word_count"] = match.group(1) + match.group(2) + "字"
        else:
            info["word_count"] = "Unknown"
        info["summary"] = soup.select_one("div.book-intro p").get_text(
            separator="\n", strip=True
        )
        # volumes
        vols = []
        for vol_div in soup.select("div.volume-wrap div.volume"):
            name = _get_volume_name(vol_div)
            chaps = []
            for li in vol_div.select("li"):
                a = li.select_one("a")
                chaps.append(
                    {
                        "title": a.get_text(strip=True),
                        "url": a["href"].strip(),
                        "chapterId": _chapter_url_to_id(a["href"]),
                    }
                )
            vols.append({"volume_name": name, "chapters": chaps})
        info["volumes"] = vols
    except Exception as e:
        logger.warning("[Parser] Error parsing book info: %s", e)
    return info
