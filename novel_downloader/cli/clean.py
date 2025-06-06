#!/usr/bin/env python3
"""
novel_downloader.cli.clean
--------------------------

CLI subcommands for clean resources.
"""

import shutil
from argparse import Namespace, _SubParsersAction
from pathlib import Path

from novel_downloader.utils.constants import (
    CONFIG_DIR,
    DATA_DIR,
    JS_SCRIPT_DIR,
    LOGGER_DIR,
    MODEL_CACHE_DIR,
    REC_CHAR_MODEL_REPO,
)
from novel_downloader.utils.i18n import t


def register_clean_subcommand(subparsers: _SubParsersAction) -> None:  # type: ignore
    parser = subparsers.add_parser("clean", help=t("help_clean"))

    parser.add_argument("--logs", action="store_true", help=t("clean_logs"))
    parser.add_argument("--cache", action="store_true", help=t("clean_cache"))
    parser.add_argument("--data", action="store_true", help=t("clean_data"))
    parser.add_argument("--config", action="store_true", help=t("clean_config"))
    parser.add_argument("--models", action="store_true", help=t("clean_models"))
    parser.add_argument("--all", action="store_true", help=t("clean_all"))
    parser.add_argument("-y", "--yes", action="store_true", help=t("clean_yes"))

    parser.add_argument("--hf-cache", action="store_true", help=t("clean_hf_cache"))
    parser.add_argument(
        "--hf-cache-all", action="store_true", help=t("clean_hf_cache_all")
    )

    parser.set_defaults(func=handle_clean)


def handle_clean(args: Namespace) -> None:
    targets: list[Path] = []

    if args.hf_cache_all:
        try:
            if _clean_model_repo_cache(all=True):
                print(t("clean_hf_cache_all_done"))
        except Exception as e:
            print(t("clean_hf_cache_all_fail", err=str(e)))
    elif args.hf_cache:
        try:
            if _clean_model_repo_cache(repo_id=REC_CHAR_MODEL_REPO):
                print(t("clean_hf_model_done", repo=REC_CHAR_MODEL_REPO))
            else:
                print(t("clean_hf_model_not_found", repo=REC_CHAR_MODEL_REPO))
        except Exception as e:
            print(t("clean_hf_model_fail", err=str(e)))

    if args.all:
        if not args.yes:
            confirm = prompt(t("clean_confirm"), default="n")
            if confirm.lower() != "y":
                print(t("clean_cancelled"))
                return
        targets = [
            LOGGER_DIR,
            JS_SCRIPT_DIR,
            DATA_DIR,
            CONFIG_DIR,
            MODEL_CACHE_DIR,
        ]
    else:
        if args.logs:
            targets.append(LOGGER_DIR)
        if args.cache:
            targets.append(JS_SCRIPT_DIR)
        if args.data:
            targets.append(DATA_DIR)
        if args.config:
            targets.append(CONFIG_DIR)
        if args.models:
            targets.append(MODEL_CACHE_DIR)

    if not targets and not args.hf_cache and not args.hf_cache_all:
        print(t("clean_nothing"))
        return

    for path in targets:
        _delete_path(path)


def prompt(message: str, default: str = "n") -> str:
    """
    Prompt the user for input with a default option.

    :param message: The prompt message to display to the user.
    :param default: The default value to use if the user provides no input ("y" or "n").
    :return: The user's input (lowercased), or the default value if no input is given.
    """
    try:
        full_prompt = f"{message} [{'Y/n' if default.lower() == 'y' else 'y/N'}]: "
        response = input(full_prompt).strip().lower()
        return response if response else default.lower()
    except (KeyboardInterrupt, EOFError):
        print("\n" + "Cancelled.")
    return default.lower()


def _delete_path(p: Path) -> None:
    if p.exists():
        if p.is_file():
            p.unlink()
        else:
            shutil.rmtree(p, ignore_errors=True)
        print(f"[clean] {t('clean_deleted')}: {p}")
    else:
        print(f"[clean] {t('clean_not_found')}: {p}")


def _clean_model_repo_cache(
    repo_id: str | None = None,
    all: bool = False,
) -> bool:
    """
    Delete Hugging Face cache for a specific repo.
    """
    from huggingface_hub import scan_cache_dir

    cache_info = scan_cache_dir()

    if all:
        targets = cache_info.repos
    elif repo_id:
        targets = [r for r in cache_info.repos if r.repo_id == repo_id]
    else:
        return False

    strategy = cache_info.delete_revisions(
        *[rev.commit_hash for r in targets for rev in r.revisions]
    )
    print(f"[clean] Will free {strategy.expected_freed_size_str}")
    strategy.execute()
    return True
