#!/usr/bin/env python3
"""
novel_downloader.infra.fontocr
------------------------------

Font-based OCR utilities for parsing and restoring obfuscated text.
"""

__all__ = ["get_font_ocr"]
__version__ = "4.0"

from .loader import get_font_ocr
