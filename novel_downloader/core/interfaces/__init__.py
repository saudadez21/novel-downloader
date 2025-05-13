#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.interfaces
--------------------------------

This package centralizes the protocol definitions used across the
system to promote interface-based design and type-safe dependency
injection.

Included protocols:
- DownloaderProtocol
- ParserProtocol
- RequesterProtocol
- SaverProtocol
"""

from .async_downloader_protocol import AsyncDownloaderProtocol
from .async_requester_protocol import AsyncRequesterProtocol
from .downloader_protocol import DownloaderProtocol
from .parser_protocol import ParserProtocol
from .requester_protocol import RequesterProtocol
from .saver_protocol import SaverProtocol

__all__ = [
    "AsyncDownloaderProtocol",
    "AsyncRequesterProtocol",
    "DownloaderProtocol",
    "ParserProtocol",
    "RequesterProtocol",
    "SaverProtocol",
]
