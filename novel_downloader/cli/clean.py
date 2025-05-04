#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.cli.clean
-----------------------------

"""

import shutil
from pathlib import Path
from typing import List, Optional

import click

from novel_downloader.utils.constants import (
    CONFIG_DIR,
    DATA_DIR,
    JS_SCRIPT_DIR,
    LOGGER_DIR,
    MODEL_CACHE_DIR,
    REC_CHAR_MODEL_REPO,
    STATE_DIR,
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


def clean_model_repo_cache(repo_id: Optional[str] = None, all: bool = False) -> bool:
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


@click.command(name="clean", help=t("help_clean"))  # type: ignore
@click.option("--logs", is_flag=True, help=t("clean_logs"))  # type: ignore
@click.option("--cache", is_flag=True, help=t("clean_cache"))  # type: ignore
@click.option("--state", is_flag=True, help=t("clean_state"))  # type: ignore
@click.option("--data", is_flag=True, help=t("clean_data"))  # type: ignore
@click.option("--config", is_flag=True, help=t("clean_config"))  # type: ignore
@click.option("--models", is_flag=True, help=t("clean_models"))  # type: ignore
@click.option("--hf-cache", is_flag=True, help=t("clean_hf_cache"))  # type: ignore
@click.option("--hf-cache-all", is_flag=True, help=t("clean_hf_cache_all"))  # type: ignore
@click.option("--all", is_flag=True, help=t("clean_all"))  # type: ignore
@click.option("--yes", is_flag=True, help=t("clean_yes"))  # type: ignore
def clean_cli(
    logs: bool,
    cache: bool,
    state: bool,
    data: bool,
    config: bool,
    models: bool,
    hf_cache: bool,
    hf_cache_all: bool,
    all: bool,
    yes: bool,
) -> None:
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
            STATE_DIR,
            DATA_DIR,
            CONFIG_DIR,
            MODEL_CACHE_DIR,
        ]
    else:
        if logs:
            targets.append(LOGGER_DIR)
        if cache:
            targets.append(JS_SCRIPT_DIR)
        if state:
            targets.append(STATE_DIR)
        if data:
            targets.append(DATA_DIR)
        if config:
            targets.append(CONFIG_DIR)
        if models:
            targets.append(MODEL_CACHE_DIR)

    if hf_cache_all:
        try:
            if clean_model_repo_cache(all=True):
                click.echo(t("clean_hf_cache_all_done"))
        except Exception as e:
            click.echo(t("clean_hf_cache_all_fail", err=e))
    elif hf_cache:
        try:
            if clean_model_repo_cache(REC_CHAR_MODEL_REPO):
                click.echo(t("clean_hf_model_done", repo=REC_CHAR_MODEL_REPO))
            else:
                click.echo(t("clean_hf_model_not_found", repo=REC_CHAR_MODEL_REPO))
        except Exception as e:
            click.echo(t("clean_hf_model_fail", err=e))

    if not targets and not hf_cache and not hf_cache_all:
        click.echo(t("clean_nothing"))
        return

    for path in targets:
        delete_path(path)
