#!/usr/bin/env python3
"""
novel_downloader.apps.cli.commands.clean
----------------------------------------

"""

import shutil
from argparse import ArgumentParser, Namespace
from pathlib import Path

from novel_downloader.apps.cli import ui
from novel_downloader.infra.i18n import t
from novel_downloader.infra.paths import (
    CONFIG_DIR,
    DATA_DIR,
    JS_SCRIPT_DIR,
    LOGGER_DIR,
)

from .base import Command


class CleanCmd(Command):
    name = "clean"
    help = t("Clear application logs, caches, and configs")

    @classmethod
    def add_arguments(cls, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--logs", action="store_true", help=t("Clear log directory")
        )
        parser.add_argument(
            "--cache", action="store_true", help=t("Clear script and cookie cache")
        )
        parser.add_argument("--data", action="store_true", help=t("Clear data files"))
        parser.add_argument(
            "--config", action="store_true", help=t("Clear configuration files")
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help=t("Clear all settings, caches, and data files"),
        )
        parser.add_argument(
            "-y", "--yes", action="store_true", help=t("Skip confirmation prompt")
        )

    @classmethod
    def run(cls, args: Namespace) -> None:
        targets: list[Path] = []

        if args.all:
            if not args.yes and (
                not ui.confirm(
                    t("Are you sure you want to delete all local data?"), default=False
                )
            ):
                ui.warn(t("Clean operation cancelled."))
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
            ui.warn(t("No clean option specified."))
            return

        for path in targets:
            cls._delete_path(path)

    @staticmethod
    def _delete_path(p: Path) -> None:
        """Delete file or directory at `p`, printing a colored result line."""
        if p.exists():
            with ui.status(t("Cleaning {path}...").format(path=p)):
                try:
                    if p.is_file():
                        p.unlink()
                    else:
                        shutil.rmtree(p, ignore_errors=True)
                    ui.success(t("Deleted {path}").format(path=p))
                except Exception as e:
                    ui.error(
                        t("Failed to delete {path}: {err}").format(path=p, err=str(e))
                    )
        else:
            ui.warn(t("Not found: {path}").format(path=p))
