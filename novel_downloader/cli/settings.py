#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.cli.settings
-----------------------------

Commands to configure novel downloader settings.
"""

import click
from click import Context

from novel_downloader.config import save_config_file, save_rules_as_json
from novel_downloader.utils.i18n import t
from novel_downloader.utils.state import state_mgr


@click.group(name="settings", help=t("settings_help"))  # type: ignore
def settings_cli() -> None:
    """Configure downloader settings."""
    pass


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
