#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.cli.clean
-----------------------------

"""

import shutil
from pathlib import Path
from typing import List

import click

from novel_downloader.utils.constants import (
    DEFAULT_USER_DATA_DIR,
    JS_SCRIPT_DIR,
    LOGGER_DIR,
    SETTING_FILE,
    SITE_RULES_FILE,
    STATE_FILE,
)
from novel_downloader.utils.i18n import t


def delete_path(p: Path) -> None:
    if p.exists():
        if p.is_file():
            p.unlink()
        else:
            shutil.rmtree(p, ignore_errors=True)
        click.echo(f"[clean] {t('clean_deleted')}: {p}")
    else:
        click.echo(f"[clean] {t('clean_not_found')}: {p}")


@click.command(name="clean", help=t("help_clean"))  # type: ignore
@click.option("--logs", is_flag=True, help=t("clean_logs"))  # type: ignore
@click.option("--cache", is_flag=True, help=t("clean_cache"))  # type: ignore
@click.option("--state", is_flag=True, help=t("clean_state"))  # type: ignore
@click.option("--all", is_flag=True, help=t("clean_all"))  # type: ignore
@click.option("--yes", is_flag=True, help=t("clean_yes"))  # type: ignore
def clean_cli(logs: bool, cache: bool, state: bool, all: bool, yes: bool) -> None:
    targets: List[Path] = []

    if all:
        if not yes:
            confirm = click.prompt(t("clean_confirm"), default="n")
            if confirm.lower() != "y":
                click.echo(t("clean_cancelled"))
                return
        targets = [
            LOGGER_DIR,
            JS_SCRIPT_DIR,
            DEFAULT_USER_DATA_DIR,
            STATE_FILE,
            SETTING_FILE,
            SITE_RULES_FILE,
        ]
    else:
        if logs:
            targets.append(LOGGER_DIR)
        if cache:
            targets.extend([JS_SCRIPT_DIR, DEFAULT_USER_DATA_DIR])
        if state:
            targets.append(STATE_FILE)

    if not targets:
        click.echo(t("clean_nothing"))
        return

    for path in targets:
        delete_path(path)
