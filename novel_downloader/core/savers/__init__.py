#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.savers
----------------------------

This module defines saver classes for different novel platforms.

Currently supported platforms:
- Qidian (起点中文网)
- CommonSaver (通用)
"""

from .common_saver import CommonSaver
from .qidian_saver import QidianSaver

__all__ = [
    "CommonSaver",
    "QidianSaver",
]
