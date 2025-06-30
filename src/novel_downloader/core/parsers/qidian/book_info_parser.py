#!/usr/bin/env python3
"""
novel_downloader.core.parsers.qidian.book_info_parser
-----------------------------------------------------

This module provides parsing of Qidian book info pages.

It extracts metadata such as title, author, cover URL, update
time, status, word count, summary, and volume-chapter structure.
"""

import logging
from typing import Any

from lxml import html

logger = logging.getLogger(__name__)

_AUTHOR_XPATH = (
    'string(//div[contains(@class, "book-info")]//a[contains(@class, "writer")])'
)


def _chapter_url_to_id(url: str) -> str:
    return url.rstrip("/").split("/")[-1]


def _get_volume_name(
    vol_elem: html.HtmlElement,
) -> str:
    """
    Extracts the volume title from a <div class="volume"> element using lxml.
    Ignores <a> tags, and extracts text from other elements.
    """
    h3_candidates = vol_elem.xpath(".//h3")
    if not h3_candidates:
        return ""
    texts = vol_elem.xpath(".//h3//text()[not(ancestor::a)]")
    full_text = "".join(texts).strip()
    return full_text.split(chr(183))[0].strip()


def parse_book_info(html_str: str) -> dict[str, Any]:
    """
    Extract metadata: title, author, cover_url, update_time, status,
    word_count, summary, and volumes with chapters.

    :param html_str: Raw HTML of the book info page.
    :return: A dict containing book metadata.
    """
    info: dict[str, Any] = {}
    try:
        doc = html.fromstring(html_str)

        book_name = doc.xpath('string(//h1/em[@id="bookName"])').strip()
        info["book_name"] = book_name

        author = doc.xpath(_AUTHOR_XPATH).strip()
        info["author"] = author

        cover_url = doc.xpath('string(//div[@class="book-img"]//img/@src)').strip()
        info["cover_url"] = cover_url

        update_raw = (
            doc.xpath('string(//span[contains(@class, "update-time")])')
            .replace("更新时间", "")
            .strip()
        )
        info["update_time"] = update_raw

        status = doc.xpath('string(//p[@class="tag"]/span[@class="blue"][1])').strip()
        info["serial_status"] = status

        tags = doc.xpath('//p[@class="tag"]/a[@class="red"]/text()')
        info["tags"] = [t.strip() for t in tags if t.strip()]

        wc_number = doc.xpath("string(//p[em and cite][1]/em[1])").strip()
        wc_unit = doc.xpath("string(//p[em and cite][1]/cite[1])").strip()
        info["word_count"] = (
            (wc_number + wc_unit) if wc_number and wc_unit else "Unknown"
        )

        summary = doc.xpath('string(//p[@class="intro"])').strip()
        info["summary_brief"] = summary

        intro_list = doc.xpath('//div[@class="book-intro"]/p')[0]
        detail_intro = "\n".join(intro_list.itertext()).strip()
        info["summary"] = detail_intro

        volumes = []
        for vol_div in doc.xpath('//div[@class="volume-wrap"]/div[@class="volume"]'):
            volume_name = _get_volume_name(vol_div)
            chapters = []
            for li in vol_div.xpath(".//li"):
                a = li.xpath(".//a")[0] if li.xpath(".//a") else None
                if a is None or "href" not in a.attrib:
                    continue
                href = a.attrib["href"].strip()
                title = "".join(a.itertext()).strip()
                chapters.append(
                    {
                        "title": title,
                        "url": href,
                        "chapterId": _chapter_url_to_id(href),
                    }
                )
            volumes.append({"volume_name": volume_name, "chapters": chapters})
        info["volumes"] = volumes

    except Exception as e:
        logger.warning("[Parser] Error parsing book info: %s", e)

    return info
