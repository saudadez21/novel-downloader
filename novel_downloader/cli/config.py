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

from novel_downloader.config import save_config_file, save_rules_as_json
from novel_downloader.utils.constants import DEFAULT_SETTINGS_PATHS
from novel_downloader.utils.i18n import t
from novel_downloader.utils.logger import setup_logging
from novel_downloader.utils.state import state_mgr

# from novel_downloader.utils.hash_store import img_hash_store


def register_config_subcommand(subparsers: _SubParsersAction) -> None:  # type: ignore
    parser = subparsers.add_parser("config", help=t("help_config"))
    config_subparsers = parser.add_subparsers(dest="subcommand", required=True)

    _register_init(config_subparsers)
    _register_set_lang(config_subparsers)
    _register_set_config(config_subparsers)
    _register_update_rules(config_subparsers)
    _register_set_cookies(config_subparsers)
    # _register_add_hash(config_subparsers)


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


def _register_update_rules(subparsers: _SubParsersAction) -> None:  # type: ignore
    parser = subparsers.add_parser("update-rules", help=t("settings_update_rules_help"))
    parser.add_argument("path", type=str, help="Path to TOML/YAML/JSON rule file")
    parser.set_defaults(func=_handle_update_rules)


def _register_set_cookies(subparsers: _SubParsersAction) -> None:  # type: ignore
    parser = subparsers.add_parser("set-cookies", help=t("settings_set_cookies_help"))
    parser.add_argument("site", nargs="?", help="Site identifier")
    parser.add_argument("cookies", nargs="?", help="Cookies string")
    parser.set_defaults(func=_handle_set_cookies)


# def _register_add_hash(subparsers: _SubParsersAction) -> None:  # type: ignore
#     parser = subparsers.add_parser("add-hash", help=t("settings_add_hash_help"))
#     parser.add_argument("--path", type=str, help=t("settings_add_hash_path_help"))
#     parser.set_defaults(func=_handle_add_hash)


def _handle_init(args: Namespace) -> None:
    setup_logging()
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


def _handle_update_rules(args: Namespace) -> None:
    try:
        save_rules_as_json(args.path)
        print(t("settings_update_rules", path=args.path))
    except Exception as e:
        print(t("settings_update_rules_fail", err=str(e)))
        raise


def _handle_set_cookies(args: Namespace) -> None:
    site = args.site or input(t("settings_set_cookies_prompt_site") + ": ").strip()
    cookies = (
        args.cookies or input(t("settings_set_cookies_prompt_payload") + ": ").strip()
    )

    try:
        state_mgr.set_cookies(site, cookies)
        print(t("settings_set_cookies_success", site=site))
    except Exception as e:
        print(t("settings_set_cookies_fail", err=str(e)))
        raise


# def _handle_add_hash(args: Namespace) -> None:
#     if args.path:
#         try:
#             img_hash_store.add_from_map(args.path)
#             img_hash_store.save()
#             print(t("settings_add_hash_loaded", path=args.path))
#         except Exception as e:
#             print(t("settings_add_hash_load_fail", err=str(e)))
#             raise
#     else:
#         print(t("settings_add_hash_prompt_tip"))
#         while True:
#             img_path = input(t("settings_add_hash_prompt_img") + ": ").strip()
#             if not img_path or img_path.lower() in {"exit", "quit"}:
#                 break
#             if not Path(img_path).exists():
#                 print(t("settings_add_hash_path_invalid"))
#                 continue

#             label = input(t("settings_add_hash_prompt_label") + ": ").strip()
#             if not label or label.lower() in {"exit", "quit"}:
#                 break

#             try:
#                 img_hash_store.add_image(img_path, label)
#                 print(t("settings_add_hash_added", img=img_path, label=label))
#             except Exception as e:
#                 print(t("settings_add_hash_failed", err=str(e)))

#         img_hash_store.save()
#         print(t("settings_add_hash_saved"))
