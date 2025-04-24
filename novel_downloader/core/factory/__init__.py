#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.core.factory
-----------------------------

This package provides factory methods for dynamically retrieving components
based on runtime parameters such as site name or content type.
"""

from .requester_factory import get_requester

__all__ = [
    "get_requester",
]
