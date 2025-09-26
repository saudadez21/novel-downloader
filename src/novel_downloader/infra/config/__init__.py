#!/usr/bin/env python3
"""
novel_downloader.infra.config
-----------------------------

Unified interface for loading and adapting configuration files.
"""

__all__ = [
    "copy_default_config",
    "get_config_value",
    "load_config",
    "save_config",
    "save_config_file",
    "ConfigAdapter",
]

from .adapter import ConfigAdapter
from .file_io import (
    copy_default_config,
    get_config_value,
    load_config,
    save_config,
    save_config_file,
)
