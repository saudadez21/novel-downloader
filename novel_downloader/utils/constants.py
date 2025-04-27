#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.utils.constants
--------------------------------

Constants and default paths used throughout the NovelDownloader project.
"""

from pathlib import Path

from platformdirs import user_config_dir

# Basic identity
PACKAGE_NAME = "novel_downloader"  # Python package name
APP_NAME = "NovelDownloader"  # Display name (used in logs, help text, etc.)
APP_DIR_NAME = "novel_downloader"  # Directory name for platformdirs
LOGGER_NAME = PACKAGE_NAME  # Root logger name

# Base config directory (e.g. ~/AppData/Local/novel_downloader/)
BASE_CONFIG_DIR = Path(user_config_dir(APP_DIR_NAME, appauthor=False))

LOGGER_DIR = BASE_CONFIG_DIR / "logs"
STATE_FILE = BASE_CONFIG_DIR / "state.json"
SETTING_FILE = BASE_CONFIG_DIR / "settings.yaml"
SITE_RULES_FILE = BASE_CONFIG_DIR / "site_rules.json"
DEFAULT_USER_DATA_DIR = BASE_CONFIG_DIR / "browser_data"
DEFAULT_USER_PROFILE_NAME = "Profile_1"

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/134.0.0.0 Safari/537.36"
)

DEFAULT_HEADERS = {"User-Agent": DEFAULT_USER_AGENT}
DEFAULT_ACCEPT = (
    "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
)

DEFAULT_USER_HEADERS = {
    "Accept": DEFAULT_ACCEPT,
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en,zh;q=0.9,zh-CN;q=0.8",
    "User-Agent": DEFAULT_USER_AGENT,
    "Connection": "keep-alive",
}
