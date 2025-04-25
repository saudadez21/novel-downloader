#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.savers.qidian_saver
-----------------------------------------

This module provides the `QidianSaver` class for handling the saving process
of novels sourced from Qidian (起点中文网). It implements the platform-specific
logic required to structure and export novel content into desired formats.
"""

from novel_downloader.config.models import SaverConfig

from .common_saver import CommonSaver


class QidianSaver(CommonSaver):
    def __init__(self, config: SaverConfig):
        super().__init__(config, site="qidian")


__all__ = ["QidianSaver"]
