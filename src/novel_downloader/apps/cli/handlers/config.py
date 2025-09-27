#!/usr/bin/env python3
"""
novel_downloader.apps.cli.handlers.config
-----------------------------------------

"""

from pathlib import Path
from typing import Any

from novel_downloader.apps.cli import ui
from novel_downloader.infra.config import copy_default_config, load_config
from novel_downloader.infra.i18n import t


def load_or_init_config(config_path: Path | None) -> dict[str, Any] | None:
    """
    Load the config file, or interactively create one if missing.

    :param config_path: Path to config file (or None to use default).

    :return: Config data if successful, otherwise None.
    """
    try:
        return load_config(config_path)
    except FileNotFoundError:
        if config_path is None:
            config_path = Path("settings.toml")
        ui.warn(t("No config found at {path}.").format(path=str(config_path.resolve())))
        if ui.confirm(t("Would you like to create a default config?"), default=True):
            copy_default_config(config_path)
            ui.success(
                t("Created default config at {path}.").format(
                    path=str(config_path.resolve())
                )
            )
        else:
            ui.error(t("Cannot continue without a config file."))
        return None

    except ValueError as e:
        ui.error(t("Failed to load configuration: {err}").format(err=str(e)))
        return None
