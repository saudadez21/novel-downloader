#!/usr/bin/env python3
"""
novel_downloader.utils.fontocr
------------------------------

Lazy-loading interface for FontOCR. Provides a safe entry point
to obtain an OCR utility instance if optional dependencies are available.
"""

__all__ = ["get_font_ocr"]
__version__ = "4.0"

from .loader import get_font_ocr
