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
from functools import lru_cache, wraps
from importlib.abc import Traversable
from importlib.resources import files
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar, Union, cast

import yaml

from ..utils.constants import LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

T = TypeVar("T", bound=Callable[..., Any])


def cached_load_config(func: T) -> T:
    cached = lru_cache(maxsize=1)(func)
    wrapped = wraps(func)(cached)
    return cast(T, wrapped)


def resolve_config_path(
    config_path: Optional[Union[str, Path]]
) -> Optional[Union[Path, Traversable]]:
    """
    Determine which config file path to use.
    Priority:
    1. User-specified path (if valid)
    2. Internal base.yaml fallback
    """
    if config_path:
        path = Path(config_path).expanduser().resolve()
        if path.is_file():
            return path
        logger.warning("[config] Specified config file not found: %s", path)

    # Fallback to internal base.yaml
    try:
        base_yaml = files("novel_downloader.defaults").joinpath("base.yaml")
        logger.info("[config] Using internal base.yaml fallback")
        return base_yaml
    except Exception as e:
        logger.error("[config] Failed to resolve internal base.yaml: %s", e)
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


__all__ = ["load_config"]
