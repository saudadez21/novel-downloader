#!/usr/bin/env python3
"""
novel_downloader.utils.constants
--------------------------------

Constants and default paths used throughout the NovelDownloader project.
"""

from importlib.resources import files
from pathlib import Path

from platformdirs import user_config_path

# -----------------------------------------------------------------------------
# Application identity
# -----------------------------------------------------------------------------
PACKAGE_NAME = "novel_downloader"  # Python package name
APP_NAME = "NovelDownloader"  # Display name
APP_DIR_NAME = "novel_downloader"  # Directory name for platformdirs
LOGGER_NAME = PACKAGE_NAME  # Root logger name

SUPPORTED_SITES = {
    "biquge",
    "esjzone",
    "linovelib",
    "qianbi",
    "qidian",
    "sfacg",
    "yamibo",
}

# -----------------------------------------------------------------------------
# Base directories
# -----------------------------------------------------------------------------
# Base config directory (e.g. ~/AppData/Local/novel_downloader/)
BASE_CONFIG_DIR = Path(user_config_path(APP_DIR_NAME, appauthor=False))
WORK_DIR = Path.cwd()
PACKAGE_ROOT: Path = Path(__file__).parent.parent
LOCALES_DIR: Path = PACKAGE_ROOT / "locales"

# Subdirectories under BASE_CONFIG_DIR
LOGGER_DIR = WORK_DIR / "logs"
JS_SCRIPT_DIR = BASE_CONFIG_DIR / "scripts"
DATA_DIR = BASE_CONFIG_DIR / "data"
CONFIG_DIR = BASE_CONFIG_DIR / "config"
MODEL_CACHE_DIR = BASE_CONFIG_DIR / "models"

# -----------------------------------------------------------------------------
# Default file paths
# -----------------------------------------------------------------------------
STATE_FILE = DATA_DIR / "state.json"
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
BASE_CONFIG_PATH = files("novel_downloader.resources.config").joinpath("settings.toml")

DEFAULT_SETTINGS_PATHS = [
    BASE_CONFIG_PATH,
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
LINOVELIB_FONT_MAP_PATH = files("novel_downloader.resources.json").joinpath(
    "linovelib_font_map.json"
)

# JavaScript
QD_DECRYPT_SCRIPT_PATH = files("novel_downloader.resources.js_scripts").joinpath(
    "qidian_decrypt_node.js"
)

# Text Files
BLACKLIST_PATH = files("novel_downloader.resources.text").joinpath("blacklist.txt")

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
