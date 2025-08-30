#!/usr/bin/env python3
"""
novel_downloader.utils.cookies
------------------------------

Utility for normalizing cookie input from user configuration.
"""

__all__ = ["parse_cookies", "get_cookie_value"]

import json
from collections.abc import Mapping
from http.cookies import SimpleCookie
from pathlib import Path


def parse_cookies(cookies: str | Mapping[str, str]) -> dict[str, str]:
    """
    Parse cookies from a string or dictionary into a standard dictionary.

    Supports input like:
      * `"key1=value1; key2=value2"`
      * `{"key1": "value1", "key2": "value2"}`

    :param cookies: Cookie string or dict-like object (e.g., from config)
    :return: A normalized cookie dictionary (key -> value)
    :raises TypeError: If the input is neither string nor dict-like
    """
    if isinstance(cookies, str):
        filtered = "; ".join(pair for pair in cookies.split(";") if "=" in pair)
        parsed = SimpleCookie()
        parsed.load(filtered)
        return {k: v.value for k, v in parsed.items()}
    elif isinstance(cookies, Mapping):
        return {str(k).strip(): str(v).strip() for k, v in cookies.items()}
    raise TypeError("Unsupported cookie format: must be str or dict-like")


def get_cookie_value(state_files: list[Path], key: str) -> str:
    for state_file in state_files:
        try:
            with state_file.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            continue

        cookies = data.get("cookies", [])
        for cookie in cookies:
            if cookie.get("name") != key:
                continue
            value = cookie.get("value")
            if isinstance(value, str):
                return value
    return ""
