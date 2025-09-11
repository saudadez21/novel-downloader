#!/usr/bin/env python3
"""
novel_downloader.core.exporters
-------------------------------

Exporter implementations for saving books in various formats across different sources
"""

__all__ = ["get_exporter"]

from .registry import get_exporter
