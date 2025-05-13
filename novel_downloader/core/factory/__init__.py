#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.factory
-----------------------------

This package provides factory methods for dynamically retrieving components
based on runtime parameters such as site name or content type.
"""

from .downloader_factory import (
    get_async_downloader,
    get_downloader,
    get_sync_downloader,
)
from .parser_factory import get_parser
from .requester_factory import (
    get_async_requester,
    get_requester,
    get_sync_requester,
)
from .saver_factory import get_saver

__all__ = [
    "get_async_downloader",
    "get_downloader",
    "get_sync_downloader",
    "get_parser",
    "get_async_requester",
    "get_requester",
    "get_sync_requester",
    "get_saver",
]
