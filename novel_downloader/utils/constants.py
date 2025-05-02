#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.utils.constants
--------------------------------

Constants and default paths used throughout the NovelDownloader project.
"""

from importlib.resources import files
from pathlib import Path

from platformdirs import user_config_dir

# Basic identity
PACKAGE_NAME = "novel_downloader"  # Python package name
APP_NAME = "NovelDownloader"  # Display name (used in logs, help text, etc.)
APP_DIR_NAME = "novel_downloader"  # Directory name for platformdirs
LOGGER_NAME = PACKAGE_NAME  # Root logger name

# Base config directory (e.g. ~/AppData/Local/novel_downloader/)
BASE_CONFIG_DIR = Path(user_config_dir(APP_DIR_NAME, appauthor=False))

PACKAGE_ROOT: Path = Path(__file__).parent.parent

LOCALES_DIR = PACKAGE_ROOT / "locales"

LOGGER_DIR = BASE_CONFIG_DIR / "logs"
JS_SCRIPT_DIR = BASE_CONFIG_DIR / "js_script"
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

DEFAULT_IMAGE_SUFFIX = ".jpg"
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

BASE_CONFIG_PATH = files("novel_downloader.defaults").joinpath("base.yaml")

# CSS Styles
CSS_MAIN_PATH = files("novel_downloader.resources.css_styles").joinpath("main.css")
CSS_VOLUME_INTRO_PATH = files("novel_downloader.resources.css_styles").joinpath(
    "volume-intro.css"
)

# Images
VOLUME_BORDER_IMAGE_PATH = files("novel_downloader.resources.images").joinpath(
    "volume_border.png"
)

# JSON
REPLACE_WORD_MAP_PATH = files("novel_downloader.resources.json").joinpath(
    "replace_word_map.json"
)

# JavaScript
QD_DECRYPT_SCRIPT_PATH = files("novel_downloader.resources.js_scripts").joinpath(
    "qidian_decrypt_node.js"
)

# Text Files
BLACKLIST_PATH = files("novel_downloader.resources.text").joinpath("blacklist.txt")

EPUB_IMAGE_FOLDER = "Images"
EPUB_TEXT_FOLDER = "Text"
