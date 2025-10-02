#!/usr/bin/env python3
"""
novel_downloader.usecases.config
--------------------------------
"""

from pathlib import Path
from typing import Any

from novel_downloader.infra.config import copy_default_config, load_config

from .protocols import ConfigUI


def load_or_init_config(
    config_path: Path | None, config_ui: ConfigUI
) -> dict[str, Any] | None:
    try:
        return load_config(config_path)
    except FileNotFoundError:
        if config_path is None:
            config_path = Path("settings.toml")

        config_ui.on_missing(config_path)
        if config_ui.confirm_create():
            copy_default_config(config_path)
            config_ui.on_created(config_path)
        else:
            config_ui.on_abort()
        return None

    except ValueError as e:
        config_ui.on_invalid(e)
        return None
