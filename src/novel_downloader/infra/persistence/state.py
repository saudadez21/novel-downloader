#!/usr/bin/env python3
"""
novel_downloader.infra.persistence.state
----------------------------------------

State management for user preferences and runtime flags.
"""

__all__ = ["StateManager", "state_mgr"]

import json
from pathlib import Path
from typing import Any

from novel_downloader.infra.paths import STATE_FILE


class StateManager:
    """
    Manages persistent state for user preferences and runtime flags.
    """

    def __init__(self, path: Path = STATE_FILE) -> None:
        self._path = path
        self._data = self._load()

    def get_language(self) -> str:
        """
        Load the user's language preference.

        :return: Language code string
        """
        return self._data.get("lang") or "zh_CN"

    def set_language(self, lang: str) -> None:
        """
        Save the user's language preference.

        :param lang: Language code
        """
        self._data["lang"] = lang
        self._save()

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


state_mgr = StateManager()
