#!/usr/bin/env python3
"""
novel_downloader.core.parsers
-----------------------------

Parser implementations for extracting book metadata and
chapter content from various sources
"""

__all__ = ["get_parser"]

from .registry import get_parser
