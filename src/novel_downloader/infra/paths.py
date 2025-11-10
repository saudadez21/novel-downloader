#!/usr/bin/env python3
"""
novel_downloader.infra.paths
----------------------------

"""

from importlib.resources import files
from pathlib import Path

from platformdirs import user_config_path

PACKAGE_NAME = "novel_downloader"  # Python package name

# -----------------------------------------------------------------------------
# User-writable directories & files
# -----------------------------------------------------------------------------

# Base config directory (e.g. ~/AppData/Local/novel_downloader/)
USER_CONFIG_DIR = user_config_path(PACKAGE_NAME, appauthor=False)

# Subdirectories
CONFIG_DIR = USER_CONFIG_DIR / "config"
DATA_DIR = USER_CONFIG_DIR / "data"
JS_SCRIPT_DIR = USER_CONFIG_DIR / "scripts"
LOGGER_DIR = Path.cwd() / "logs"

# Files under user dirs
STATE_FILE = DATA_DIR / "state.json"
SETTING_FILE = CONFIG_DIR / "settings.json"

# Default config filename (used when copying embedded template)
DEFAULT_CONFIG_FILENAME = "settings.toml"

# -----------------------------------------------------------------------------
# Embedded resources
# -----------------------------------------------------------------------------

RES = files("novel_downloader.resources")

# Config
DEFAULT_CONFIG_FILE = RES.joinpath("config", "settings.sample.toml")

# CSS Styles
EPUB_CSS_MAIN_PATH = RES.joinpath("css_styles", "epub_main.css")
EPUB_CSS_INTRO_PATH = RES.joinpath("css_styles", "epub_intro.css")
HTML_CSS_INDEX_PATH = RES.joinpath("css_styles", "html_index.css")
HTML_CSS_CHAPTER_PATH = RES.joinpath("css_styles", "html_chapter.css")

# Images
# VOLUME_BORDER_IMAGE_PATH = RES.joinpath("images", "volume_border.png")
VOLUME_BORDER_IMAGE_PATH = RES.joinpath("images", "volume_border_tinify.png")

# JSON
FANQIENOVEL_MAP_PATH = RES.joinpath("json", "fanqienovel.json")
HONGXIUZHAO_MAP_PATH = RES.joinpath("json", "hongxiuzhao.json")
LINOVELIB_MAP_PATH = RES.joinpath("json", "linovelib.json")
N69YUE_MAP_PATH = RES.joinpath("json", "n69yue.json")
XIGUASHUWU_MAP_PATH = RES.joinpath("json", "xiguashuwu.json")
YODU_MAP_PATH = RES.joinpath("json", "yodu.json")

# JavaScript
EXPR_TO_JSON_SCRIPT_PATH = RES.joinpath("js_scripts", "expr_to_json.js")
QD_DECRYPT_SCRIPT_PATH = RES.joinpath("js_scripts", "qidian_decrypt_node.js")
QQ_DECRYPT_SCRIPT_PATH = RES.joinpath("js_scripts", "qq_decrypt_node.js")
HTML_JS_MAIN_PATH = RES.joinpath("js_scripts", "html_main.js")
