#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.config
------------------------

Unified interface for loading and adapting configuration files.

This module provides:
- load_config: loads YAML config from file path with fallback support
- ConfigAdapter: maps raw config + site name to structured config models
- Configuration dataclasses: RequesterConfig, DownloaderConfig, etc.
"""

from .adapter import ConfigAdapter
from .loader import load_config
from .models import (
    DownloaderConfig,
    ParserConfig,
    RequesterConfig,
    SaverConfig,
)

__all__ = [
    "load_config",
    "ConfigAdapter",
    "RequesterConfig",
    "DownloaderConfig",
    "ParserConfig",
    "SaverConfig",
]
