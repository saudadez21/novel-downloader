#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.savers.epub_utils
---------------------------------------

This package provides utility functions for constructing EPUB files,
including:

- CSS inclusion (create_css_items)
- EPUB book initialization (init_epub)
- Chapter text-to-HTML conversion (chapter_txt_to_html)
- Volume intro HTML generation (create_volume_intro)
"""

from .css_builder import create_css_items
from .initializer import init_epub
from .text_to_html import chapter_txt_to_html, generate_book_intro_html
from .volume_intro import create_volume_intro

__all__ = [
    "create_css_items",
    "init_epub",
    "chapter_txt_to_html",
    "create_volume_intro",
    "generate_book_intro_html",
]
