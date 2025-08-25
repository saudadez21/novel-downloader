#!/usr/bin/env python3
"""
novel_downloader.config
-----------------------

Unified interface for loading and adapting configuration files.
"""

__all__ = [
    "load_config",
    "save_config",
    "save_config_file",
    "ConfigAdapter",
]

from .adapter import ConfigAdapter
from .file_io import (
    load_config,
    save_config,
    save_config_file,
)
