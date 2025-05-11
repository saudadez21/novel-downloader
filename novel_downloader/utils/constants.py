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

# -----------------------------------------------------------------------------
# Application identity
# -----------------------------------------------------------------------------
PACKAGE_NAME = "novel_downloader"  # Python package name
APP_NAME = "NovelDownloader"  # Display name
APP_DIR_NAME = "novel_downloader"  # Directory name for platformdirs
LOGGER_NAME = PACKAGE_NAME  # Root logger name


# -----------------------------------------------------------------------------
# Base directories
# -----------------------------------------------------------------------------
# Base config directory (e.g. ~/AppData/Local/novel_downloader/)
BASE_CONFIG_DIR = Path(user_config_dir(APP_DIR_NAME, appauthor=False))
PACKAGE_ROOT: Path = Path(__file__).parent.parent
LOCALES_DIR: Path = PACKAGE_ROOT / "locales"

# Subdirectories under BASE_CONFIG_DIR
LOGGER_DIR = BASE_CONFIG_DIR / "logs"
JS_SCRIPT_DIR = BASE_CONFIG_DIR / "scripts"
STATE_DIR = BASE_CONFIG_DIR / "state"
DATA_DIR = BASE_CONFIG_DIR / "data"
CONFIG_DIR = BASE_CONFIG_DIR / "config"
MODEL_CACHE_DIR = BASE_CONFIG_DIR / "models"

# -----------------------------------------------------------------------------
# Default file paths
# -----------------------------------------------------------------------------
STATE_FILE = STATE_DIR / "state.json"
HASH_STORE_FILE = DATA_DIR / "image_hashes.json"
SETTING_FILE = CONFIG_DIR / "settings.json"
SITE_RULES_FILE = CONFIG_DIR / "site_rules.json"
DEFAULT_USER_DATA_DIR = DATA_DIR / "browser_data"


# -----------------------------------------------------------------------------
# Default preferences & headers
# -----------------------------------------------------------------------------
DEFAULT_USER_PROFILE_NAME = "Profile_1"
DEFAULT_IMAGE_SUFFIX = ".jpg"

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

# -----------------------------------------------------------------------------
# Embedded resources (via importlib.resources)
# -----------------------------------------------------------------------------
BASE_CONFIG_PATH = files("novel_downloader.resources.config").joinpath("settings.yaml")
BASE_RULE_PATH = files("novel_downloader.resources.config").joinpath("rules.toml")

DEFAULT_SETTINGS_PATHS = [
    BASE_CONFIG_PATH,
    BASE_RULE_PATH,
]

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

# -----------------------------------------------------------------------------
# EPUB defaults
# -----------------------------------------------------------------------------
EPUB_IMAGE_FOLDER = "Images"
EPUB_TEXT_FOLDER = "Text"

EPUB_OPTIONS = {
    # guide 是 EPUB 2 的一个部分, 包含封面, 目录, 索引等重要导航信息
    "epub2_guide": True,
    # landmark 是 EPUB 3 用来标识重要页面 (如目录, 封面, 起始页) 的 <nav> 结构
    "epub3_landmark": True,
    # EPUB 3 允许提供一个 page list, 让电子书在不同设备上仍然保持相对一致的分页结构
    "epub3_pages": True,
    # 这个名字会出现在 EPUB 阅读器的导航栏
    "landmark_title": "Guide",
    # 这个名字会显示在 EPUB 阅读器的分页导航栏
    "pages_title": "Pages",
    # 是否根据 book.spine 的排列顺序自动设置 EPUB 阅读器的 page-progression-direction
    "spine_direction": True,
    # 控制 EPUB 阅读器的默认翻页方向 (LTR 或 RTL)
    "package_direction": False,
    # 是否为 EPUB 书籍中的章节 添加播放顺序
    "play_order": {"enabled": True, "start_from": 1},
}

# ---------------------------------------------------------------------
# Pretrained model registry (e.g. used in font recovery or OCR)
# ---------------------------------------------------------------------

# Hugging Face model repo for character recognition
REC_CHAR_MODEL_REPO = "saudadez/rec_chinese_char"

# Required files to be downloaded for the model
REC_CHAR_MODEL_FILES = [
    "inference.pdmodel",
    "inference.pdiparams",
    "rec_custom_keys.txt",
    "char_freq.json",
]

REC_CHAR_VECTOR_FILES = [
    "char_vectors.npy",
    "char_vectors.txt",
]

REC_IMAGE_SHAPE_MAP = {
    "v1.0": "3,32,32",
    "v2.0": "3,48,48",
}
