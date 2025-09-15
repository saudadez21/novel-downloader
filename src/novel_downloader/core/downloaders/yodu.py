#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.yodu
--------------------------------------

Downloader implementation for yodu novels, with chapter ID repair logic.
"""

from novel_downloader.core.downloaders.n23qb import N23qbDownloader
from novel_downloader.core.downloaders.registry import register_downloader


@register_downloader(site_keys=["yodu"])
class YoduDownloader(N23qbDownloader):
    """
    Downloader for yodu (有度中文网) novels.

    Repairs missing chapter IDs by following 'next' links, then downloads
    each chapter as a unit (fetch -> parse -> enqueue storage).
    """
