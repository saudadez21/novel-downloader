#!/usr/bin/env python3
"""
novel_downloader.utils.i18n
---------------------------

"""

__all__ = ["t"]

import gettext
from importlib.resources import files

from novel_downloader.utils.state import state_mgr

LANG_MAP = {
    "zh": "zh_CN",
    "en": "en_US",
}


def get_translation(lang: str) -> gettext.NullTranslations:
    try:
        mo_path = files("novel_downloader.locales").joinpath(
            lang, "LC_MESSAGES", "messages.mo"
        )
        with mo_path.open("rb") as f:
            return gettext.GNUTranslations(f)
    except FileNotFoundError:
        return gettext.NullTranslations()


_lang = state_mgr.get_language()
_locale = LANG_MAP.get(_lang, _lang)
_translation = get_translation(_locale)

t = _translation.gettext
