#!/usr/bin/env python3
"""
novel_downloader.core.savers.epub_utils
---------------------------------------

This package provides utility functions for constructing EPUB files,
including:

- CSS inclusion (css_builder)
- Image embedding (image_loader)
- EPUB book initialization (initializer)
- Chapter text-to-HTML conversion (text_to_html)
- Volume intro HTML generation (volume_intro)
"""

from .css_builder import create_css_items
from .image_loader import add_images_from_dir, add_images_from_dirs
from .initializer import init_epub
from .text_to_html import (
    chapter_txt_to_html,
    generate_book_intro_html,
    inline_remote_images,
)
from .volume_intro import create_volume_intro

__all__ = [
    "create_css_items",
    "add_images_from_dir",
    "add_images_from_dirs",
    "init_epub",
    "chapter_txt_to_html",
    "create_volume_intro",
    "generate_book_intro_html",
    "inline_remote_images",
]
