#!/usr/bin/env python3
"""
novel_downloader.cli.commands.clean
-----------------------------------

"""

import shutil
from argparse import ArgumentParser, Namespace
from pathlib import Path

from novel_downloader.cli import ui
from novel_downloader.utils.constants import (
    CONFIG_DIR,
    DATA_DIR,
    JS_SCRIPT_DIR,
    LOGGER_DIR,
)
from novel_downloader.utils.i18n import t

from .base import Command


class CleanCmd(Command):
    name = "clean"
    help = t("help_clean")

    @classmethod
    def add_arguments(cls, parser: ArgumentParser) -> None:
        parser.add_argument("--logs", action="store_true", help=t("clean_logs"))
        parser.add_argument("--cache", action="store_true", help=t("clean_cache"))
        parser.add_argument("--data", action="store_true", help=t("clean_data"))
        parser.add_argument("--config", action="store_true", help=t("clean_config"))
        parser.add_argument("--all", action="store_true", help=t("clean_all"))
        parser.add_argument("-y", "--yes", action="store_true", help=t("clean_yes"))

    @classmethod
    def run(cls, args: Namespace) -> None:
        targets: list[Path] = []

        if args.all:
            if not args.yes and not ui.confirm(t("clean_confirm"), default=False):
                ui.warn(t("clean_cancelled"))
                return
            targets = [LOGGER_DIR, JS_SCRIPT_DIR, DATA_DIR, CONFIG_DIR]
        else:
            if args.logs:
                targets.append(LOGGER_DIR)
            if args.cache:
                targets.append(JS_SCRIPT_DIR)
            if args.data:
                targets.append(DATA_DIR)
            if args.config:
                targets.append(CONFIG_DIR)

        if not targets:
            ui.warn(t("clean_nothing"))
            return

        for path in targets:
            cls._delete_path(path)

    @staticmethod
    def _delete_path(p: Path) -> None:
        """Delete file or directory at `p`, printing a colored result line."""
        if p.exists():
            with ui.status(t("cleaning", path=p)):
                try:
                    if p.is_file():
                        p.unlink()
                    else:
                        shutil.rmtree(p, ignore_errors=True)
                    ui.success(t("clean_deleted", path=p))
                except Exception as e:
                    ui.error(t("clean_failed", path=p, err=str(e)))
        else:
            ui.warn(t("clean_not_found", path=p))
