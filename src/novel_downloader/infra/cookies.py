#!/usr/bin/env python3
"""
novel_downloader.infra.cookies
------------------------------

Utility for normalizing cookie input from user configuration.
"""

__all__ = ["parse_cookies", "get_cookie_value"]

import functools
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


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
        result: dict[str, str] = {}
        for part in cookies.split(";"):
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            key, value = key.strip(), value.strip()
            if not key:
                continue
            result[key] = value
        return result
    elif isinstance(cookies, Mapping):
        return {str(k).strip(): str(v).strip() for k, v in cookies.items()}
    raise TypeError("Unsupported cookie format: must be str or dict-like")


def get_cookie_value(state_files: list[Path], key: str) -> str:
    for state_file in state_files:
        if not state_file.exists():
            continue

        try:
            mtime = state_file.stat().st_mtime
        except OSError:
            continue

        data = load_state_file(state_file, mtime)
        cookies = data.get("cookies", [])
        value = next(
            (
                c.get("value")
                for c in cookies
                if c.get("name") == key and isinstance(c.get("value"), str)
            ),
            None,
        )
        if isinstance(value, str):
            return value
    return ""


@functools.cache
def load_state_file(state_file: Path, mtime: float = 0.0) -> dict[str, Any]:
    try:
        return json.loads(state_file.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError):
        return {}
