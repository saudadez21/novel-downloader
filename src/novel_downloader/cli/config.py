#!/usr/bin/env python3
"""
novel_downloader.cli.config
---------------------------

CLI subcommands for configuration management.
"""

import shutil
from argparse import Namespace, _SubParsersAction
from importlib.resources import as_file
from pathlib import Path

from novel_downloader.config import save_config_file
from novel_downloader.utils.constants import DEFAULT_SETTINGS_PATHS
from novel_downloader.utils.i18n import t
from novel_downloader.utils.state import state_mgr


def register_config_subcommand(subparsers: _SubParsersAction) -> None:  # type: ignore
    parser = subparsers.add_parser("config", help=t("help_config"))
    config_subparsers = parser.add_subparsers(dest="subcommand", required=True)

    _register_init(config_subparsers)
    _register_set_lang(config_subparsers)
    _register_set_config(config_subparsers)


def _register_init(subparsers: _SubParsersAction) -> None:  # type: ignore
    parser = subparsers.add_parser("init", help=t("settings_init_help"))
    parser.add_argument(
        "--force", action="store_true", help=t("settings_init_force_help")
    )
    parser.set_defaults(func=_handle_init)


def _register_set_lang(subparsers: _SubParsersAction) -> None:  # type: ignore
    parser = subparsers.add_parser("set-lang", help=t("settings_set_lang_help"))
    parser.add_argument("lang", choices=["zh", "en"], help="Language code")
    parser.set_defaults(func=_handle_set_lang)


def _register_set_config(subparsers: _SubParsersAction) -> None:  # type: ignore
    parser = subparsers.add_parser("set-config", help=t("settings_set_config_help"))
    parser.add_argument("path", type=str, help="Path to YAML config file")
    parser.set_defaults(func=_handle_set_config)


def _handle_init(args: Namespace) -> None:
    cwd = Path.cwd()

    for resource in DEFAULT_SETTINGS_PATHS:
        target_path = cwd / resource.name
        should_copy = True

        if target_path.exists():
            if args.force:
                print(t("settings_init_overwrite", filename=resource.name))
            else:
                print(t("settings_init_exists", filename=resource.name))
                resp = (
                    input(
                        t("settings_init_confirm_overwrite", filename=resource.name)
                        + " [y/N]: "
                    )
                    .strip()
                    .lower()
                )
                should_copy = resp == "y"

        if not should_copy:
            print(t("settings_init_skip", filename=resource.name))
            continue

        try:
            with as_file(resource) as actual_path:
                shutil.copy(actual_path, target_path)
                print(t("settings_init_copy", filename=resource.name))
        except Exception as e:
            print(t("settings_init_error", filename=resource.name, err=str(e)))
            raise


def _handle_set_lang(args: Namespace) -> None:
    state_mgr.set_language(args.lang)
    print(t("settings_set_lang", lang=args.lang))


def _handle_set_config(args: Namespace) -> None:
    try:
        save_config_file(args.path)
        print(t("settings_set_config", path=args.path))
    except Exception as e:
        print(t("settings_set_config_fail", err=str(e)))
        raise
