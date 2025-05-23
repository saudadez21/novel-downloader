#!/usr/bin/env python3
"""
novel_downloader.core.parsers.qidian.shared.book_info_parser
------------------------------------------------------------

This module provides parsing of Qidian book info pages.

It extracts metadata such as title, author, cover URL, update
time, status, word count, summary, and volume-chapter structure.
"""

import logging
import re
from typing import Any

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


def safe_select_text(
    soup: Tag,
    selector: str,
    *,
    separator: str = "",
    strip: bool = False,
    default: str = "",
) -> str:
    """
    Safely select the first element matching a CSS selector and return its text.

    :param soup: A BeautifulSoup Tag or sub-tree to query.
    :param selector: A CSS selector string.
    :param separator: Separator to use between strings when joining.
    :param strip: Whether to strip whitespace from the result.
    :param default: Value to return if no element is found.
    :return: The element's text, or `default` if not found.
    """
    tag = soup.select_one(selector)
    return (
        tag.get_text(separator=separator, strip=strip)
        if isinstance(tag, Tag)
        else default
    )


def safe_select_attr(
    soup: Tag,
    selector: str,
    attr: str,
    *,
    default: str = "",
) -> str:
    """
    Safely select the first element matching a CSS selector and return one attributes.

    :param soup: A BeautifulSoup Tag or sub-tree to query.
    :param selector: A CSS selector string.
    :param attr: The attribute name to retrieve from the selected element.
    :param default: Value to return if no element or attribute is found.
    :return: The attribute's value stripped of whitespace, or `default` if not found.
    """
    tag = soup.select_one(selector)
    if isinstance(tag, Tag) and attr in tag.attrs:
        value = tag.attrs[attr]
        if isinstance(value, list):
            return " ".join(value).strip()
        elif isinstance(value, str):
            return value.strip()
    return default


def parse_book_info(html_str: str) -> dict[str, Any]:
    """
    Extract metadata: title, author, cover_url, update_time, status,
    word_count, summary, and volumes with chapters.

    :param html_str: Raw HTML of the book info page.
    :return: A dict containing book metadata.
    """
    info: dict[str, Any] = {}
    try:
        soup = html_to_soup(html_str)
        info["book_name"] = safe_select_text(soup, "em#bookName", strip=True)
        info["author"] = safe_select_text(soup, "a.writer", strip=True)
        info["cover_url"] = safe_select_attr(soup, "div.book-img img", "src")
        info["update_time"] = (
            safe_select_text(soup, "span.book-update-time", strip=True)
            .replace("更新时间", "")
            .strip()
        )
        info["serial_status"] = safe_select_text(soup, "span.blue", strip=True)

        # Word count via regex fallback
        match = re.search(r"<em>([\d.]+)</em>\s*<cite>(.*?)字</cite>", html_str)
        info["word_count"] = (
            f"{match.group(1)}{match.group(2)}字" if match else "Unknown"
        )

        info["summary"] = safe_select_text(
            soup, "div.book-intro p", separator="\n", strip=True
        )
        # volumes
        vols = []
        for vol_div in soup.select("div.volume-wrap div.volume"):
            name = _get_volume_name(vol_div)
            chaps = []
            for li in vol_div.select("li"):
                a = li.select_one("a")
                if not isinstance(a, Tag) or "href" not in a.attrs:
                    continue
                href_val = a["href"]
                if isinstance(href_val, list):
                    href = href_val[0].strip()
                else:
                    href = str(href_val).strip()
                chaps.append(
                    {
                        "title": a.get_text(strip=True),
                        "url": href,
                        "chapterId": _chapter_url_to_id(href),
                    }
                )
            vols.append({"volume_name": name, "chapters": chaps})
        info["volumes"] = vols
    except Exception as e:
        logger.warning("[Parser] Error parsing book info: %s", e)
    return info
