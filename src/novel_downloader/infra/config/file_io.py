#!/usr/bin/env python3
"""
novel_downloader.infra.config.file_io
-------------------------------------

Utilities to load, validate, and save configuration files.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from novel_downloader.infra.paths import DEFAULT_CONFIG_FILE

logger = logging.getLogger(__name__)


def _resolve_file_path(
    user_path: str | Path | None,
    local_filename: list[str],
) -> Path | None:
    """
    Resolve the file path to use based on a prioritized lookup order.

    Priority:
      1. A user-specified path (if provided and exists)
      2. A file in the current working directory with the given name

    :return: Resolved Path or None if not found.
    """
    if user_path:
        path = Path(user_path).expanduser().resolve()
        if path.is_file():
            return path
        logger.warning("Specified file not found: %s", path)

    for name in local_filename:
        local_path = (Path.cwd() / name).resolve()
        if local_path.is_file():
            logger.debug("Using local file: %s", local_path)
            return local_path

    return None


def _validate_dict(data: Any, path: Path, format: str) -> dict[str, Any]:
    """
    Validate that the parsed config is a dictionary.

    :param data: The loaded content to validate.
    :param path: Path to the original config file (used for logging).
    :param format: Format name ('json', 'toml', etc.) for log context.
    :return: The original data if valid, otherwise an empty dict.
    """
    if not isinstance(data, dict):
        logger.warning(
            "%s content is not a dictionary: %s",
            format.upper(),
            path,
        )
        return {}
    return data


def _load_by_extension(path: Path) -> dict[str, Any]:
    """
    Load a configuration file by its file extension.

    Supports: .toml, .json

    :param path: Path to the configuration file.
    :return: Parsed configuration as a dictionary.
    :raises ValueError: If the file extension is unsupported.
    """
    ext = path.suffix.lower()

    if ext == ".json":
        try:
            with path.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            raise ValueError(f"Invalid JSON in {path}: {e}") from e
        return _validate_dict(data, path, "json")

    elif ext == ".toml":
        try:
            import tomllib

            with path.open("rb") as f:
                data = tomllib.load(f)
        except Exception as e:
            raise ValueError(f"Invalid TOML in {path}: {e}") from e
        return _validate_dict(data, path, "toml")

    raise ValueError(f"Unsupported config file extension: {ext}")


def load_config(
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Load configuration data from a Toml file.

    :param config_path: Optional path to the Toml configuration file.
    :return: Parsed configuration as a dict.
    :raises FileNotFoundError: If no viable config is found.
    :raises ValueError: If parsing fails.
    """
    path = _resolve_file_path(
        user_path=config_path,
        local_filename=["settings.toml", "settings.json"],
    )

    if not path or not path.is_file():
        raise FileNotFoundError("No valid config file found.")

    logger.debug("Loading configuration from: %s", path)
    return _load_by_extension(path)


def get_config_value(keys: list[str], default: Any) -> Any:
    """
    Safely retrieve a nested config value from the current config.
    """
    cur = load_config()
    for i, k in enumerate(keys):
        if not isinstance(cur, dict):
            return default
        if i == len(keys) - 1:
            val = cur.get(k, default)
            return val if isinstance(val, type(default)) else default
        cur = cur.get(k, {})
    return default


def copy_default_config(target: Path) -> None:
    """
    Copy the bundled default config to the given target path.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    data = DEFAULT_CONFIG_FILE.read_bytes()
    target.write_bytes(data)
