#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.parsers.qidian_parser.shared
--------------------------------------------------

Shared parsing utilities for Qidian parser components.

This subpackage provides common functions used across
different Qidian parsing strategies. It encapsulates logic for:

- Parsing the SSR-rendered page context and chapter metadata.
- Determining access control and encryption status of chapters.
- Basic HTML preprocessing and fallback parsing behavior.
- Extracting structured book info from the main book page.
"""

from .book_info_parser import parse_book_info
from .helpers import (
    can_view_chapter,
    extract_chapter_info,
    find_ssr_page_context,
    html_to_soup,
    is_encrypted,
    is_vip,
    vip_status,
)

__all__ = [
    "parse_book_info",
    "html_to_soup",
    "is_vip",
    "can_view_chapter",
    "is_encrypted",
    "vip_status",
    "find_ssr_page_context",
    "extract_chapter_info",
]
