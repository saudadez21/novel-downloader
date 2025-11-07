#!/usr/bin/env python3
"""
novel_downloader.infra.cookies
------------------------------

Utility for normalizing cookie input from user configuration.
"""

__all__ = ["parse_cookies", "CookieStore"]

import json
from collections.abc import Mapping
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


class CookieStore:
    """
    A simple cookie storage and loader utility that reads cookies from multiple
    supported client formats and caches them in memory.

    Supported cookie files (by default):
      * aiohttp.cookies
      * curl_cffi.cookies
      * httpx.cookies
    """

    DEFAULT_FILENAMES = ["aiohttp.cookies", "curl_cffi.cookies", "httpx.cookies"]

    def __init__(self, cookies_dir: Path, filenames: list[str] | None = None) -> None:
        """
        Initialize a new CookieStore.

        :param cookies_dir: Directory containing cookie state files.
        :param filenames: Optional list of cookie filenames to read.
        """
        self.cookies_dir = cookies_dir
        self.filenames = filenames or self.DEFAULT_FILENAMES
        self.cache: dict[str, str] = {}
        self.mtimes: dict[str, float] = {}

    def get(self, key: str) -> str:
        """
        Retrieve a cookie value by name.

        :param key: The name of the cookie to retrieve.
        :return: The cookie value if found, otherwise an empty string.
        """
        self.load_all()
        return self.cache.get(key, "")

    def load_all(self) -> None:
        """
        Load or refresh cookies from all known cookie files.

        For each configured cookie file, this method:
          * Checks whether the file exists.
          * Compares its modification time (`mtime`) to the last cached value.
          * If changed, reads and parses the JSON content.
          * Extracts `name` and `value` pairs into the in-memory cache.
        """
        for filename in self.filenames:
            state_file = self.cookies_dir / filename
            if not state_file.exists():
                continue
            try:
                mtime = state_file.stat().st_mtime
                if self.mtimes.get(filename) == mtime:
                    continue
                self.mtimes[filename] = mtime
                data = json.loads(state_file.read_text(encoding="utf-8")) or []
                for c in data:
                    if "name" in c and "value" in c:
                        self.cache[c["name"]] = c["value"]
            except (OSError, json.JSONDecodeError):
                continue
