#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core
---------------------

This package serves as the core layer of the novel_downloader system.

It provides factory methods for constructing key components required for
downloading and processing online novel content, including:

- Downloader: Handles the full download lifecycle of a book or a batch of books.
- Parser: Extracts structured data from HTML or SSR content.
- Requester: Sends HTTP requests and manages sessions, including login if required.
- Saver: Responsible for exporting downloaded data into various output formats.
"""

from .factory import get_downloader, get_parser, get_requester, get_saver

__all__ = [
    "get_downloader",
    "get_parser",
    "get_requester",
    "get_saver",
]
