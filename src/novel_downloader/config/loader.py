#!/usr/bin/env python3
"""
novel_downloader.config.loader
------------------------------

Provides functionality to load Toml configuration files into Python
dictionaries, with robust error handling and fallback support.
"""

import json
import logging
from pathlib import Path
from typing import Any

from novel_downloader.utils.cache import cached_load_config
from novel_downloader.utils.constants import SETTING_FILE

logger = logging.getLogger(__name__)


def resolve_file_path(
    user_path: str | Path | None,
    local_filename: str | list[str],
    fallback_path: Path,
) -> Path | None:
    """
    Resolve the file path to use based on a prioritized lookup order.

    Priority:
        1. A user-specified path (if provided and exists)
        2. A file in the current working directory with the given name
        3. A globally registered fallback path

    :param user_path: Optional user-specified file path.
    :param local_filename: File name to check in the current working directory.
    :param fallback_path: Fallback path used if other options are not available.
    :return: A valid Path object if found, otherwise None.
    """
    if user_path:
        path = Path(user_path).expanduser().resolve()
        if path.is_file():
            return path
        logger.warning("[config] Specified file not found: %s", path)

    filenames = [local_filename] if isinstance(local_filename, str) else local_filename
    for name in filenames:
        local_path = Path.cwd() / name
        if local_path.is_file():
            logger.debug("[config] Using local file: %s", local_path)
            return local_path

    if fallback_path.is_file():
        logger.debug("[config] Using fallback file: %s", fallback_path)
        return fallback_path

    logger.warning("[config] No file found at any location for: %s", local_filename)
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
            "[config] %s content is not a dictionary: %s",
            format.upper(),
            path,
        )
        return {}
    return data


def _load_by_extension(path: Path) -> dict[str, Any]:
    """
    Load a configuration file by its file extension.

    Supports `.toml`, `.json`, and `.yaml`/`.yml` formats.

    :param path: Path to the configuration file.
    :return: Parsed configuration as a dictionary.
    :raises ValueError: If the file extension is unsupported.
    """
    ext = path.suffix.lower()
    if ext == ".json":
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
            return _validate_dict(data, path, "json")

    elif ext == ".toml":
        import tomllib

        with path.open("rb") as f:
            data = tomllib.load(f)
            return _validate_dict(data, path, "toml")

    elif ext in {".yaml", ".yml"}:
        try:
            import yaml
        except ImportError as err:
            raise ImportError(
                "YAML config support requires PyYAML. "
                "Install it via: pip install PyYAML"
            ) from err
        with path.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            return _validate_dict(data, path, "yaml")

    else:
        raise ValueError(f"Unsupported config file extension: {ext}")


@cached_load_config
def load_config(
    config_path: str | Path | None = None,
) -> dict[str, Any]:
    """
    Load configuration data from a Toml file.

    :param config_path: Optional path to the Toml configuration file.
    :return:            Parsed configuration as a dict.
    """
    path = resolve_file_path(
        user_path=config_path,
        local_filename=[
            "settings.toml",
            "settings.yaml",
            "settings.yml",
            "settings.json",
        ],
        fallback_path=SETTING_FILE,
    )

    if not path or not path.is_file():
        raise FileNotFoundError("No valid config file found.")

    try:
        return _load_by_extension(path)
    except Exception as e:
        logger.warning("[config] Failed to load config file: %s", e)
    return {}


def save_config_file(
    source_path: str | Path,
    output_path: str | Path = SETTING_FILE,
) -> None:
    """
    Validate a TOML/YAML/JSON config file, load it into a dict,
    and then dump it as JSON to the internal SETTING_FILE.

    :param source_path: The user-provided TOML file path.
    :param output_path: Destination path to save the config (default: SETTING_FILE).
    """
    source = Path(source_path).expanduser().resolve()
    output = Path(output_path).expanduser().resolve()

    if not source.is_file():
        raise FileNotFoundError(f"Source file not found: {source}")

    try:
        data = _load_by_extension(source)
    except (ValueError, ImportError) as e:
        logger.error("[config] Failed to load config file: %s", e)
        raise ValueError(f"Invalid config file: {source}") from e

    output.parent.mkdir(parents=True, exist_ok=True)

    try:
        with output.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error("[config] Failed to write config JSON '%s': %s", output, e)
        raise

    logger.info("[config] Configuration successfully saved to JSON: %s", output)
    return


__all__ = ["load_config"]
