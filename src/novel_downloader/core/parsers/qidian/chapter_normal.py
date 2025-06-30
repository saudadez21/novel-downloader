#!/usr/bin/env python3
"""
novel_downloader.core.parsers.qidian.chapter_normal
---------------------------------------------------

Parser logic for extracting readable text from Qidian chapters
that use plain (non-encrypted) browser-rendered HTML.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from lxml import html

from novel_downloader.models import ChapterDict
from novel_downloader.utils.text_utils import truncate_half_lines

from .utils import (
    extract_chapter_info,
    find_ssr_page_context,
    get_decryptor,
    is_duplicated,
    vip_status,
)

if TYPE_CHECKING:
    from .main_parser import QidianParser

logger = logging.getLogger(__name__)


def parse_normal_chapter(
    parser: QidianParser,
    html_str: str,
    chapter_id: str,
) -> ChapterDict | None:
    """
    Extract structured chapter info from a normal Qidian page.

    :param html_str: Chapter HTML.
    :param chapter_id: Chapter identifier (string).
    :return: a dictionary with keys like 'id', 'title', 'content', etc.
    """
    try:
        ssr_data = find_ssr_page_context(html_str)
        chapter_info = extract_chapter_info(ssr_data)
        if not chapter_info:
            logger.warning(
                "[Parser] ssr_chapterInfo not found for chapter '%s'", chapter_id
            )
            return None

        title = chapter_info.get("chapterName", "Untitled")
        duplicated = is_duplicated(ssr_data)
        raw_html = chapter_info.get("content", "")
        chapter_id = chapter_info.get("chapterId", chapter_id)
        fkp = chapter_info.get("fkp", "")
        author_say = chapter_info.get("authorSay", "")
        update_time = chapter_info.get("updateTime", "")
        update_timestamp = chapter_info.get("updateTimestamp", 0)
        modify_time = chapter_info.get("modifyTime", 0)
        word_count = chapter_info.get("actualWords", 0)
        seq = chapter_info.get("seq", None)
        volume = chapter_info.get("extra", {}).get("volumeName", "")

        chapter_text = _parse_browser_paragraph(html_str)
        if not chapter_text:
            chapter_text = _parse_session_paragraph(
                html_str=raw_html,
                is_vip=vip_status(ssr_data),
                chapter_id=chapter_id,
                fkp=fkp,
                fuid=parser._fuid,
            )
            if not chapter_text:
                return None

        if parser._use_truncation and duplicated:
            chapter_text = truncate_half_lines(chapter_text)

        return {
            "id": str(chapter_id),
            "title": title,
            "content": chapter_text,
            "extra": {
                "author_say": author_say.strip() if author_say else "",
                "updated_at": update_time,
                "update_timestamp": update_timestamp,
                "modify_time": modify_time,
                "word_count": word_count,
                "duplicated": duplicated,
                "seq": seq,
                "volume": volume,
                "encrypted": False,
            },
        }
    except Exception as e:
        logger.warning(
            "[Parser] parse error for normal chapter '%s': %s", chapter_id, e
        )
    return None


def _parse_browser_paragraph(html_str: str) -> str:
    try:
        tree = html.fromstring(html_str)
        main = tree.xpath('//div[@id="app"]//div[@id="reader-content"]//main')
        if not main:
            return ""
        main = main[0]

        content_spans = main.xpath('.//span[contains(@class, "content-text")]')

        paragraph_texts = [
            span.text_content().strip()
            for span in content_spans
            if span.text_content().strip()
        ]

        chapter_text = "\n\n".join(paragraph_texts)
        return chapter_text

    except Exception as e:
        logger.error("[Parser] _parse_paragraph failed: %s", e)
    return ""


def _parse_session_paragraph(
    html_str: str,
    is_vip: bool,
    chapter_id: str,
    fkp: str,
    fuid: str,
) -> str:
    try:
        raw_html = html_str

        if is_vip:
            try:
                decryptor = get_decryptor()
                raw_html = decryptor.decrypt(raw_html, chapter_id, fkp, fuid)
            except Exception as e:
                logger.error("[Parser] decryption failed for '%s': %s", chapter_id, e)
                return ""

        tree = html.fromstring(raw_html)
        paras = tree.xpath(".//p")
        paragraph_texts = [
            p.text_content().strip() for p in paras if p.text_content().strip()
        ]
        return "\n\n".join(paragraph_texts)

    except Exception as e:
        logger.error("[Parser] _parse_paragraph failed: %s", e)
    return ""
