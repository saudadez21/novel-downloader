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

# -----------------------------------------------------------------------------
# Default preferences & headers
# -----------------------------------------------------------------------------

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
# Supported map
# -----------------------------------------------------------------------------

DOWNLOAD_SUPPORT_SITES = {
    "aaatxt": "3A电子书 (aaatxt)",
    "b520": "笔趣阁 (b520)",
    "biquge5": "笔趣阁 (biquge5)",
    "biquguo": "笔趣阁小说网 (biquguo)",
    "biquyuedu": "精彩小说 (biquyuedu)",
    "blqudu": "笔趣读 (blqudu)",
    "bxwx9": "笔下文学网 (bxwx9)",
    "ciluke": "思路客 (ciluke)",
    "dxmwx": "大熊猫文学网 (dxmwx)",
    "esjzone": "ESJ Zone (esjzone)",
    "fsshu": "笔趣阁 (fsshu)",
    "guidaye": "名著阅读 (guidaye)",
    "hetushu": "和图书 (hetushu)",
    "i25zw": "25中文网 (i25zw)",
    "ixdzs8": "爱下电子书 (ixdzs8)",
    "jpxs123": "精品小说网 (jpxs123)",
    "ktshu": "八一中文网 (ktshu)",
    "kunnu": "鲲弩小说 (kunnu)",
    "laoyaoxs": "老幺小说网 (laoyaoxs)",
    "lewenn": "乐文小说网 (lewenn)",
    "linovelib": "哔哩轻小说 (linovelib)",
    "lnovel": "轻小说百科 (lnovel)",
    "mangg_com": "追书网.com (mangg_com)",
    "mangg_net": "追书网.net (mangg_net)",
    "n8novel": "无限轻小说 (n8novel)",
    # "n8tsw": "笔趣阁 (n8tsw)",
    "n23ddw": "顶点小说网 (n23ddw)",
    "n23qb": "铅笔小说 (n23qb)",
    "n37yq": "三七轻小说 (n37yq)",
    "n37yue": "37阅读网 (n37yue)",
    "n71ge": "新吾爱文学 (n71ge)",
    "piaotia": "飘天文学网 (piaotia)",
    "qbtr": "全本同人小说 (qbtr)",
    "qidian": "起点中文网 (qidian)",
    "qqbook": "QQ阅读 (qqbook)",
    "quanben5": "全本小说网 (quanben5)",
    "sfacg": "SF轻小说 (sfacg)",
    "shencou": "神凑轻小说 (shencou)",
    "shu111": "书林文学 (shu111)",
    "shuhaige": "书海阁小说网 (shuhaige)",
    "tongrenquan": "同人圈 (tongrenquan)",
    "trxs": "同人小说网 (trxs)",
    "ttkan": "天天看小说 (ttkan)",
    "wanbengo": "完本神站 (wanbengo)",
    # "xiaoshuoge": "小说屋 (xiaoshuoge)",
    "xiguashuwu": "西瓜书屋 (xiguashuwu)",
    # "xs63b": "小说路上 (xs63b)",
    "xshbook": "小说虎 (xshbook)",
    "yamibo": "百合会 (yamibo)",
    "yibige": "一笔阁 (yibige)",
    "yodu": "有度中文网 (yodu)",
    "zhenhunxiaoshuo": "镇魂小说网 (zhenhunxiaoshuo)",
}

SEARCH_SUPPORT_SITES = {
    "aaatxt": "3A电子书",
    "b520": "笔趣阁 (b520)",
    "biquge5": "笔趣阁 (biquge5)",
    "biquguo": "笔趣阁小说网",
    "bxwx9": "笔下文学网",
    "ciluke": "思路客",
    "dxmwx": "大熊猫文学网",
    "esjzone": "ESJ Zone",
    "fsshu": "笔趣阁 (fsshu)",
    "hetushu": "和图书",
    "i25zw": "25中文网",
    "ixdzs8": "爱下电子书",
    "jpxs123": "精品小说网",
    "ktshu": "八一中文网",
    "laoyaoxs": "老幺小说网",
    "mangg_net": "追书网.net",
    "n8novel": "无限轻小说",
    "n23ddw": "顶点小说网",
    "n23qb": "铅笔小说",
    "n37yq": "三七轻小说",
    "n37yue": "37阅读网",
    "n71ge": "新吾爱文学",
    "piaotia": "飘天文学网",
    "qbtr": "全本同人小说",
    "qidian": "起点中文网",
    "quanben5": "全本小说网",
    "shuhaige": "书海阁小说网",
    "tongrenquan": "同人圈",
    "trxs": "同人小说网",
    "ttkan": "天天看小说",
    "wanbengo": "完本神站",
    # "xiaoshuoge": "小说屋",
    "xiguashuwu": "西瓜书屋",
    # "xs63b": "小说路上",
    "xshbook": "小说虎",
    "yodu": "有度中文网",
}
