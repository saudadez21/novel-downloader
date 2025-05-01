#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.requesters
--------------------------------

This package provides requester implementations for different novel platforms.
Each submodule corresponds to a specific site and encapsulates the logic needed
to perform network interactions, such as logging in, sending requests,
or interacting with browser/session-based sources.

Subpackages:
- common_requester: Handles all common-site requesting logic.
- qidian_requester: Handles all Qidian-related requesting logic.
"""

from .common_requester import CommonSession
from .qidian_requester import (
    QidianBrowser,
    QidianSession,
)

__all__ = [
    "CommonSession",
    "QidianBrowser",
    "QidianSession",
]
