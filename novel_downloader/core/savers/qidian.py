#!/usr/bin/env python3
"""
novel_downloader.core.savers.qidian
-----------------------------------

This module provides the `QidianSaver` class for handling the saving process
of novels sourced from Qidian (起点中文网). It implements the platform-specific
logic required to structure and export novel content into desired formats.
"""

from novel_downloader.config.models import SaverConfig

from .common import CommonSaver


class QidianSaver(CommonSaver):
    def __init__(
        self,
        config: SaverConfig,
    ):
        super().__init__(
            config,
            site="qidian",
            chap_folders=["chapters", "encrypted_chapters"],
        )


__all__ = ["QidianSaver"]
