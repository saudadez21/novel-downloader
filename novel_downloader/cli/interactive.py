#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.cli.interactive
--------------------------------

Interactive CLI mode for novel_downloader.
Supports multilingual prompt, input validation, and quit control.
"""

import click
from click import Context

from novel_downloader.cli.download import download_cli
from novel_downloader.utils.i18n import t


@click.group(  # type: ignore
    name="interactive", help=t("interactive_help"), invoke_without_command=True
)
@click.pass_context  # type: ignore
def interactive_cli(ctx: Context) -> None:
    """Interactive mode for novel selection and preview."""
    if ctx.invoked_subcommand is None:
        click.echo(t("interactive_no_sub"))

        options = [
            t("interactive_option_download"),
            t("interactive_option_browse"),
            t("interactive_option_preview"),
            t("interactive_option_exit"),
        ]
        for idx, opt in enumerate(options, 1):
            click.echo(f"{idx}. {opt}")

        choice = click.prompt(t("interactive_prompt_choice"), type=int)

        if choice == 1:
            default_site = "qidian"
            site: str = click.prompt(
                t("download_option_site", default=default_site),
                default_site,
            )
            ids_input: str = click.prompt(t("interactive_prompt_book_ids"))
            book_ids = ids_input.strip().split()
            ctx.invoke(download_cli, book_ids=book_ids, site=site)
        elif choice == 2:
            ctx.invoke(browse)
        elif choice == 3:
            ctx.invoke(preview)
        else:
            click.echo(t("interactive_exit"))
            return


@interactive_cli.command(help=t("interactive_browse_help"))  # type: ignore
@click.pass_context  # type: ignore
def browse(ctx: Context) -> None:
    """Browse available novels interactively."""
    click.echo(t("interactive_browse_start"))


@interactive_cli.command(help=t("interactive_preview_help"))  # type: ignore
@click.pass_context  # type: ignore
def preview(ctx: Context) -> None:
    """Preview chapters before downloading."""
    click.echo(t("interactive_preview_start"))
