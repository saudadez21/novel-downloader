#!/usr/bin/env python3
"""
novel_downloader.utils.state
----------------------------
State management for user preferences and runtime flags.

Supported sections:
- general: global preferences (e.g. language)
- sites: per-site flags & data (e.g. manual_login, cookies)
"""
import json
from pathlib import Path
from typing import Any

from .constants import STATE_FILE


class StateManager:
    """
    Manages persistent state for user preferences and runtime flags.
    Stores data in JSON at STATE_FILE.
    """

    def __init__(self, path: Path = STATE_FILE) -> None:
        self._path = path
        self._data = self._load()

    def _load(self) -> dict[str, Any]:
        """
        Load the configuration file into a Python dictionary.

        :return: A dict representing the full config state.
        """
        if not self._path.exists():
            return {}
        try:
            text = self._path.read_text(encoding="utf-8")
            return json.loads(text) or {}
        except Exception:
            return {}

    def _save(self) -> None:
        """
        Save a configuration dictionary to the config file.

        :param data: A dict representing the full config state to be written.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        content = json.dumps(self._data, ensure_ascii=False, indent=2)
        self._path.write_text(content, encoding="utf-8")

    def _parse_cookie_string(self, cookie_str: str) -> dict[str, str]:
        """
        Parse a Cookie header string into a dict.

        :param cookie_str: e.g. 'k1=v1; k2=v2; k3'
        :return: mapping cookie names to values (missing '=' yields empty string)
        :rtype: Dict[str, str]
        """
        cookies: dict[str, str] = {}
        for item in cookie_str.split(";"):
            item = item.strip()
            if not item:
                continue
            if "=" in item:
                k, v = item.split("=", 1)
                cookies[k.strip()] = v.strip()
            else:
                cookies[item] = ""
        return cookies

    def get_language(self) -> str:
        """
        Load the user's language preference, defaulting to 'zh'.

        :return: Language code string
        """
        lang = self._data.get("general", {}).get("lang", "zh")
        return str(lang)

    def set_language(self, lang: str) -> None:
        """
        Save the user's language preference.

        :param lang: Language code (e.g. 'zh', 'en')
        """
        self._data.setdefault("general", {})["lang"] = lang
        self._save()

    def get_manual_login_flag(self, site: str) -> bool:
        """
        Retrieve the manual login requirement flag for a specific site.

        :param site: Site identifier (e.g. 'qidian', 'bqg')
        :return: True if manual login is required (defaults to True)
        """
        val = self._data.get("sites", {}).get(site, {}).get("manual_login", True)
        return bool(val)

    def set_manual_login_flag(self, site: str, flag: bool) -> None:
        """
        Set the 'manual_login' flag for a specific site.

        :param flag: True if the site requires manual login.
        :param site: Site identifier (e.g. 'qidian', 'bqg')
        """
        sites = self._data.setdefault("sites", {})
        site_data = sites.setdefault(site, {})
        site_data["manual_login"] = flag
        self._save()

    def get_cookies(self, site: str) -> dict[str, str]:
        """
        Retrieve the persisted cookies for a specific site.

        :param site: Site identifier (e.g. 'qidian', 'bqg')
        :return: A dict mapping cookie names to values. Returns empty dict if not set.
        """
        cookies = self._data.get("sites", {}).get(site, {}).get("cookies", {})
        return {str(k): str(v) for k, v in cookies.items()}

    def set_cookies(self, site: str, cookies: str | dict[str, str]) -> None:
        """
        Persist (overwrite) the cookies for a specific site.

        :param site: Site identifier (e.g. 'qidian', 'bqg')
        :param cookies: Either a dict mapping cookie names to values,
                        or a string (JSON or 'k=v; k2=v2') to be parsed.
        :raises TypeError: if cookies is neither str nor dict
        """
        # 1) normalize to dict
        if isinstance(cookies, dict):
            cookies_dict = cookies
        elif isinstance(cookies, str):
            # try JSON first
            try:
                parsed = json.loads(cookies)
                if isinstance(parsed, dict):
                    cookies_dict = parsed  # OK!
                else:
                    raise ValueError
            except Exception:
                # fallback to "k=v; k2=v2" format
                cookies_dict = self._parse_cookie_string(cookies)
        else:
            raise TypeError("`cookies` must be a dict or a str")

        # 2) persist
        sites = self._data.setdefault("sites", {})
        site_data = sites.setdefault(site, {})
        site_data["cookies"] = {str(k): str(v) for k, v in cookies_dict.items()}
        self._save()


state_mgr = StateManager()
