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
from .loader import load_config, save_config_file
from .models import (
    BookInfoRules,
    DownloaderConfig,
    FieldRules,
    ParserConfig,
    RequesterConfig,
    RuleStep,
    SaverConfig,
    SiteProfile,
    SiteRules,
    SiteRulesDict,
    VolumesRules,
)
from .site_rules import (
    load_site_rules,
    save_rules_as_json,
)

__all__ = [
    "load_config",
    "save_config_file",
    "ConfigAdapter",
    "RequesterConfig",
    "DownloaderConfig",
    "ParserConfig",
    "SaverConfig",
    "FieldRules",
    "RuleStep",
    "SiteProfile",
    "SiteRules",
    "SiteRulesDict",
    "VolumesRules",
    "BookInfoRules",
    "load_site_rules",
    "save_rules_as_json",
]
