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
from .loader import load_config, set_setting_file
from .models import (
    DownloaderConfig,
    FieldRules,
    ParserConfig,
    RequesterConfig,
    RuleStep,
    SaverConfig,
    SiteRulesDict,
)
from .site_rules import (
    load_site_rules,
    save_rules_as_json,
)

__all__ = [
    "load_config",
    "set_setting_file",
    "ConfigAdapter",
    "RequesterConfig",
    "DownloaderConfig",
    "ParserConfig",
    "SaverConfig",
    "FieldRules",
    "RuleStep",
    "SiteRulesDict",
    "load_site_rules",
    "save_rules_as_json",
]
