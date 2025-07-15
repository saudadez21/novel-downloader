#!/usr/bin/env python3
"""
novel_downloader.config
-----------------------

Unified interface for loading and adapting configuration files.

This module provides:
- load_config: loads YAML config from file path with fallback support
- ConfigAdapter: maps raw config + site name to structured config models
"""

__all__ = [
    "load_config",
    "save_config_file",
    "ConfigAdapter",
]

from .adapter import ConfigAdapter
from .loader import load_config, save_config_file
