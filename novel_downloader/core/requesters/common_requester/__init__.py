#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.requesters.common_requester
-------------------------------------------------

This module provides the `CommonSession` class wrapper for common HTTP
request operations to novel websites. It serves as a unified access
point to import `CommonSession` without exposing lower-level modules.
"""

from .common_session import CommonSession

__all__ = ["CommonSession"]
