#!/usr/bin/env python3
"""
novel_downloader.cli.config
---------------------------

CLI subcommands for configuration file management.
"""

from __future__ import annotations

import shutil
from argparse import Namespace, _SubParsersAction
from importlib.resources import as_file
from pathlib import Path

from novel_downloader.cli import ui
from novel_downloader.config import save_config_file
from novel_downloader.utils.constants import DEFAULT_SETTINGS_PATHS
from novel_downloader.utils.i18n import t
from novel_downloader.utils.state import state_mgr


def register_config_subcommand(subparsers: _SubParsersAction) -> None:  # type: ignore
    """Register `config` with `init`, `set-lang`, and `set-config` subcommands."""
    parser = subparsers.add_parser("config", help=t("help_config"))
    config_subparsers = parser.add_subparsers(dest="subcommand", required=True)

    _register_init(config_subparsers)
    _register_set_lang(config_subparsers)
    _register_set_config(config_subparsers)


def _register_init(subparsers: _SubParsersAction) -> None:  # type: ignore
    parser = subparsers.add_parser("init", help=t("config_init_help"))
    parser.add_argument(
        "--force", action="store_true", help=t("config_init_force_help")
    )
    parser.set_defaults(func=_handle_init)


def _register_set_lang(subparsers: _SubParsersAction) -> None:  # type: ignore
    parser = subparsers.add_parser("set-lang", help=t("config_set_lang_help"))
    parser.add_argument("lang", choices=["zh", "en"], help="Language code")
    parser.set_defaults(func=_handle_set_lang)


def _register_set_config(subparsers: _SubParsersAction) -> None:  # type: ignore
    parser = subparsers.add_parser("set-config", help=t("config_set_config_help"))
    parser.add_argument("path", type=str, help="Path to YAML config file")
    parser.set_defaults(func=_handle_set_config)


def _handle_init(args: Namespace) -> None:
    """
    Copy template settings files from package resources into the current working dir.
    If the target file exists, optionally confirm overwrite (unless --force).
    """
    cwd = Path.cwd()

    for resource in DEFAULT_SETTINGS_PATHS:
        target_path = cwd / resource.name
        should_copy = True

        if target_path.exists():
            if args.force:
                ui.warn(t("config_init_overwrite", filename=resource.name))
            else:
                ui.info(t("config_init_exists", filename=resource.name))
                should_copy = ui.confirm(
                    t("config_init_confirm_overwrite", filename=resource.name),
                    default=False,
                )

        if not should_copy:
            ui.warn(t("config_init_skip", filename=resource.name))
            continue

        try:
            with as_file(resource) as actual_path:
                shutil.copy(actual_path, target_path)
                ui.success(t("config_init_copy", filename=resource.name))
        except Exception as e:
            ui.error(t("config_init_error", filename=resource.name, err=str(e)))
            raise


def _handle_set_lang(args: Namespace) -> None:
    """Set the UI language and persist in state manager."""
    state_mgr.set_language(args.lang)
    ui.success(t("config_set_lang", lang=args.lang))


def _handle_set_config(args: Namespace) -> None:
    """Persist a user-supplied TOML config path into the app config."""
    try:
        save_config_file(args.path)
        ui.success(t("config_set_config", path=args.path))
    except Exception as e:
        ui.error(t("config_set_config_fail", err=str(e)))
        raise
