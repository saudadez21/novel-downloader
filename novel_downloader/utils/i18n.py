#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.utils.i18n
---------------------------

Multilingual text dictionary and utility for CLI and interactive mode.
"""

import json
from typing import Any, Dict

from novel_downloader.utils.constants import LOCALES_DIR
from novel_downloader.utils.state import state_mgr

_TRANSLATIONS: Dict[str, Dict[str, str]] = {}

for locale_path in LOCALES_DIR.glob("*.json"):
    lang = locale_path.stem
    try:
        with open(locale_path, "r", encoding="utf-8") as f:
            _TRANSLATIONS[lang] = json.load(f)
    except Exception:
        continue


def t(key: str, **kwargs: Any) -> str:
    """
    Retrieve a localized string by key and language.

    :param key: The string key.
    :param kwargs: Optional formatting arguments.
    :return: The translated string, or the key if not found.
    """
    lang = state_mgr.get_language() or "zh"
    txt = (
        _TRANSLATIONS.get(lang, {}).get(key)
        or _TRANSLATIONS.get("en", {}).get(key)
        or key
    )
    return txt.format(**kwargs)
