#!/usr/bin/env python3
"""
novel_downloader.infra.paths
----------------------------

"""

from importlib.resources import files

from platformdirs import user_config_path

PACKAGE_NAME = "novel_downloader"  # Python package name

# Base config directory (e.g. ~/AppData/Local/novel_downloader/)
STATE_PATH = user_config_path(PACKAGE_NAME, appauthor=False) / "state.json"

RES = files("novel_downloader.resources")

# Config
DEFAULT_CONFIG_FILE = RES.joinpath("config", "settings.sample.toml")

# Default config filename (used when copying embedded template)
DEFAULT_CONFIG_FILENAME = "settings.toml"

# CSS Styles
EPUB_CSS_STYLE_PATH = RES.joinpath("css_styles", "epub_style.css")
HTML_CSS_INDEX_PATH = RES.joinpath("css_styles", "html_index.css")
HTML_CSS_CHAPTER_PATH = RES.joinpath("css_styles", "html_chapter.css")

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
