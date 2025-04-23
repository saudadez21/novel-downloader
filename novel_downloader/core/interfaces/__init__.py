#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.interfaces
--------------------------------

Collects the core protocol interfaces for parsing, requesting, and saving
book data: ParserProtocol, RequesterProtocol, and SaverProtocol.
"""

from .parser_protocol import ParserProtocol
from .requester_protocol import RequesterProtocol
from .saver_protocol import SaverProtocol

__all__ = [
    "ParserProtocol",
    "RequesterProtocol",
    "SaverProtocol",
]
