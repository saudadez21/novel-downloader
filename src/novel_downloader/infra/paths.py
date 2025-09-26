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
CSS_MAIN_PATH = RES.joinpath("css_styles", "main.css")
CSS_INTRO_PATH = RES.joinpath("css_styles", "intro.css")

# Images
# VOLUME_BORDER_IMAGE_PATH = RES.joinpath("images", "volume_border.png")
VOLUME_BORDER_IMAGE_PATH = RES.joinpath("images", "volume_border_tinify.png")

# JSON
LINOVELIB_MAP_PATH = RES.joinpath("json", "linovelib.json")
LINOVELIB_PCTHEMA_MAP_PATH = RES.joinpath("json", "linovelib_pctheme.json")
XIGUASHUWU_MAP_PATH = RES.joinpath("json", "xiguashuwu.json")
YODU_MAP_PATH = RES.joinpath("json", "yodu.json")

# JavaScript
EXPR_TO_JSON_SCRIPT_PATH = RES.joinpath("js_scripts", "expr_to_json.js")
QD_DECRYPT_SCRIPT_PATH = RES.joinpath("js_scripts", "qidian_decrypt_node.js")
QQ_DECRYPT_SCRIPT_PATH = RES.joinpath("js_scripts", "qq_decrypt_node.js")
