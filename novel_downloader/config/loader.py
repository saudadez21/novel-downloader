#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.config.loader
--------------------------------

Provides functionality to load YAML configuration files into Python
dictionaries, with robust error handling and fallback support.

This is typically used to load user-supplied or internal default config files.
"""

import logging
import shutil
from importlib.abc import Traversable
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

from novel_downloader.utils.cache import cached_load_config
from novel_downloader.utils.constants import (
    BASE_CONFIG_PATH,
    SETTING_FILE,
)

logger = logging.getLogger(__name__)


def resolve_config_path(
    config_path: Optional[Union[str, Path]]
) -> Optional[Union[Path, Traversable]]:
    """
    Resolve which configuration file to use, in this priority order:

    1. User-specified path (the `config_path` argument).
    2. `./settings.yaml` in the current working directory.
    3. The global settings file (`SETTING_FILE`).
    4. The internal default (`BASE_CONFIG_PATH`).

    Returns a Path to the first existing file, or None if none is found.
    """
    # 1. Try the user-provided path
    if config_path:
        path = Path(config_path).expanduser().resolve()
        if path.is_file():
            return path
        logger.warning("[config] Specified config file not found: %s", path)

    # 2. Try ./settings.yaml in the current working directory
    local_path = Path.cwd() / "settings.yaml"
    if local_path.is_file():
        logger.debug("[config] Using local settings.yaml at %s", local_path)
        return local_path

    # 3. Try the globally registered settings file
    if SETTING_FILE.is_file():
        logger.debug("[config] Using global settings file at %s", SETTING_FILE)
        return SETTING_FILE

    # 4. Fallback to the internal default configuration
    try:
        logger.debug(
            "[config] Falling back to internal base config at %s", BASE_CONFIG_PATH
        )
        return BASE_CONFIG_PATH
    except Exception as e:
        logger.error("[config] Failed to load internal base config: %s", e)
        return None


@cached_load_config
def load_config(config_path: Optional[Union[str, Path]]) -> Dict[str, Any]:
    """
    Load configuration data from a YAML file.

    :param config_path: Optional path to the YAML configuration file.
    :return:            Parsed configuration as a dict.
    """
    path = resolve_config_path(config_path)
    if not path or not path.is_file():
        logger.warning("[config] No valid config file found, using empty config.")
        return {}

    try:
        content = path.read_text(encoding="utf-8")
    except Exception as e:
        logger.error("[config] Failed to read config file '%s': %s", path, e)
        return {}

    try:
        data = yaml.safe_load(content)
    except yaml.YAMLError as e:
        logger.error("[config] YAML parse error in '%s': %s", path, e)
        return {}

    if data is None:
        return {}
    if not isinstance(data, dict):
        logger.warning(
            "[config] Expected dict in config file '%s', got %s",
            path,
            type(data).__name__,
        )
        return {}

    return data


def save_config_file(
    source_path: Union[str, Path], output_path: Union[str, Path] = SETTING_FILE
) -> None:
    """
    Validate a YAML config file and copy it to the application's setting path.

    :param source_path: The user-provided YAML file path.
    :param output_path: Destination path to save the config (default: SETTING_FILE).
    """
    source = Path(source_path).expanduser().resolve()
    output = Path(output_path).expanduser().resolve()

    if not source.is_file():
        raise FileNotFoundError(f"Source file not found: {source}")

    if source.suffix.lower() not in {".yaml", ".yml"}:
        raise ValueError(f"Source file must be a .yaml or .yml: {source}")

    logger.debug("[config] Checking YAML validity: %s", source)

    try:
        with source.open("r", encoding="utf-8") as f:
            yaml.safe_load(f)
    except Exception as e:
        logger.error("[config] Invalid YAML format: %s", e)
        raise ValueError(f"Invalid YAML file: {source}") from e

    logger.debug("[config] YAML validated, saving to %s", output)

    output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, output)

    logger.info("[config] Setting file successfully updated: %s", output)


__all__ = ["load_config"]
