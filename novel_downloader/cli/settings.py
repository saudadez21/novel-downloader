#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.cli.settings
-----------------------------

Commands to configure novel downloader settings.
"""

import shutil
from importlib.resources import as_file
from pathlib import Path
from typing import Optional

import click
from click import Context

from novel_downloader.config import save_config_file, save_rules_as_json
from novel_downloader.utils.constants import DEFAULT_SETTINGS_PATHS
from novel_downloader.utils.i18n import t
from novel_downloader.utils.logger import setup_logging
from novel_downloader.utils.state import state_mgr


@click.group(name="settings", help=t("settings_help"))  # type: ignore
def settings_cli() -> None:
    """Configure downloader settings."""
    setup_logging()
    pass


@settings_cli.command(name="init", help=t("settings_init_help"))  # type: ignore
@click.option("--force", is_flag=True, help=t("settings_init_force_help"))  # type: ignore
def init_settings(force: bool) -> None:
    """Initialize default settings and rules in the current directory."""
    cwd = Path.cwd()

    for resource in DEFAULT_SETTINGS_PATHS:
        target_path = cwd / resource.name
        should_copy = True

        if target_path.exists():
            if force:
                should_copy = True
                click.echo(t("settings_init_overwrite", filename=resource.name))
            else:
                click.echo(t("settings_init_exists", filename=resource.name))
                should_copy = click.confirm(
                    t("settings_init_confirm_overwrite", filename=resource.name),
                    default=False,
                )

        if not should_copy:
            click.echo(t("settings_init_skip", filename=resource.name))
            continue

        try:
            with as_file(resource) as actual_path:
                shutil.copy(actual_path, target_path)
                click.echo(t("settings_init_copy", filename=resource.name))
        except Exception as e:
            raise click.ClickException(
                t("settings_init_error", filename=resource.name, err=e)
            )


@settings_cli.command(name="set-lang", help=t("settings_set_lang_help"))  # type: ignore
@click.argument("lang", type=click.Choice(["zh", "en"]))  # type: ignore
@click.pass_context  # type: ignore
def set_language(ctx: Context, lang: str) -> None:
    """Switch language between Chinese and English."""
    state_mgr.set_language(lang)
    click.echo(t("settings_set_lang", lang=lang))


@settings_cli.command(name="set-config", help=t("settings_set_config_help"))  # type: ignore
@click.argument("path", type=click.Path(exists=True, dir_okay=False, resolve_path=True))  # type: ignore
def set_config(path: str) -> None:
    """Set and save a custom YAML configuration file."""
    try:
        save_config_file(path)
        click.echo(t("settings_set_config", path=path))
    except Exception as e:
        raise click.ClickException(t("settings_set_config_fail", err=e))


@settings_cli.command(name="update-rules", help=t("settings_update_rules_help"))  # type: ignore
@click.argument("path", type=click.Path(exists=True, dir_okay=False, resolve_path=True))  # type: ignore
def update_rules(path: str) -> None:
    """Update site rules from a TOML/YAML/JSON file."""
    try:
        save_rules_as_json(path)
        click.echo(t("settings_update_rules", path=path))
    except Exception as e:
        raise click.ClickException(t("settings_update_rules_fail", err=e))


@settings_cli.command(
    name="set-cookies", help=t("settings_set_cookies_help")
)  # type: ignore
@click.argument("site", required=False)  # type: ignore
@click.argument("cookies", required=False)  # type: ignore
@click.pass_context  # type: ignore
def set_cookies(ctx: Context, site: str, cookies: str) -> None:
    """
    Set or update cookies for a site.

    :param site: Site identifier (e.g. 'qidian', 'bqg').
                 If omitted, you will be prompted to enter it.
    :param cookies: Cookie payload. Can be a JSON string (e.g. '{"k":"v"}')
                    or a browser-style string 'k1=v1; k2=v2'.
                    If omitted, you will be prompted to enter it.
    """
    if not site:
        site = click.prompt(t("settings_set_cookies_prompt_site"), type=str)
    if not cookies:
        cookies = click.prompt(t("settings_set_cookies_prompt_payload"), type=str)

    try:
        state_mgr.set_cookies(site, cookies)
        click.echo(t("settings_set_cookies_success", site=site))
    except Exception as e:
        raise click.ClickException(t("settings_set_cookies_fail", err=e))


@settings_cli.command(name="add-hash", help=t("settings_add_hash_help"))  # type: ignore
@click.option(
    "--path",
    type=click.Path(exists=True, dir_okay=False),
    help=t("settings_add_hash_path_help"),
)  # type: ignore
def add_image_hashes(path: Optional[str]) -> None:
    """
    Add image hashes to internal store for matching.
    Can be run in interactive mode (no --path), or with a JSON file.
    """
    from novel_downloader.utils.hash_store import img_hash_store

    if path:
        try:
            img_hash_store.add_from_map(path)
            img_hash_store.save()
            click.echo(t("settings_add_hash_loaded", path=path))
        except Exception as e:
            raise click.ClickException(t("settings_add_hash_load_fail", err=str(e)))
    else:
        click.echo(t("settings_add_hash_prompt_tip"))
        while True:
            img_path = click.prompt(
                t("settings_add_hash_prompt_img"),
                type=str,
                default="",
                show_default=False,
            ).strip()
            if not img_path or img_path.lower() in {"exit", "quit"}:
                break
            if not Path(img_path).exists():
                click.echo(t("settings_add_hash_path_invalid"))
                continue

            label = click.prompt(
                t("settings_add_hash_prompt_label"),
                type=str,
                default="",
                show_default=False,
            ).strip()
            if not label or label.lower() in {"exit", "quit"}:
                break

            try:
                img_hash_store.add_image(img_path, label)
                click.echo(t("settings_add_hash_added", img=img_path, label=label))
            except Exception as e:
                click.echo(t("settings_add_hash_failed", err=str(e)))

        img_hash_store.save()
        click.echo(t("settings_add_hash_saved"))
