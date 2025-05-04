#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.cli.main
--------------------------

Unified CLI entry point. Parses arguments and delegates to parser or interactive.
"""

from typing import Optional

import click
from click import Context

from novel_downloader.cli import clean, download, interactive, settings
from novel_downloader.utils.i18n import t


@click.group(help=t("cli_help"), invoke_without_command=True)  # type: ignore
@click.option(
    "--config",
    type=click.Path(exists=True, dir_okay=False, resolve_path=True),
    default=None,
    help=t("help_config"),
)  # type: ignore
@click.pass_context  # type: ignore
def cli_main(ctx: Context, config: Optional[str]) -> None:
    """Novel Downloader CLI."""
    ctx.ensure_object(dict)
    ctx.obj["config_path"] = config

    if ctx.invoked_subcommand is None:
        click.echo(t("main_no_command"))
        ctx.invoke(interactive.interactive_cli)


# Register subcommands
cli_main.add_command(clean.clean_cli)
cli_main.add_command(download.download_cli)
cli_main.add_command(interactive.interactive_cli)
cli_main.add_command(settings.settings_cli)


if __name__ == "__main__":
    cli_main()
