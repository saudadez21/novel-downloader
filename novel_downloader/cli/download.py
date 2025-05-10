#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.cli.download
-----------------------------

Download full novels by book IDs
(supports config files, site switching, and localization prompts).
"""

from typing import List

import click
from click import Context

from novel_downloader.config import ConfigAdapter, load_config
from novel_downloader.core import (
    get_downloader,
    get_parser,
    get_requester,
    get_saver,
)
from novel_downloader.utils.i18n import t
from novel_downloader.utils.logger import setup_logging


@click.command(
    name="download",
    help=t("download_help"),
    short_help=t("download_short_help"),
)  # type: ignore
@click.argument("book_ids", nargs=-1)  # type: ignore
@click.option(
    "--site",
    default="qidian",
    show_default=True,
    help=t("download_option_site", default="qidian"),
)  # type: ignore
@click.pass_context  # type: ignore
def download_cli(ctx: Context, book_ids: List[str], site: str) -> None:
    """Download full novels by book IDs."""
    config_path = ctx.obj.get("config_path")

    click.echo(t("download_using_config", path=config_path))
    click.echo(t("download_site_info", site=site))

    config_data = load_config(config_path)
    adapter = ConfigAdapter(config=config_data, site=site)

    # Retrieve each sub-component's configuration from the adapter
    requester_cfg = adapter.get_requester_config()
    downloader_cfg = adapter.get_downloader_config()
    parser_cfg = adapter.get_parser_config()
    saver_cfg = adapter.get_saver_config()

    # If no book_ids provided on the command line, try to load them from config
    if not book_ids:
        try:
            book_ids = adapter.get_book_ids()
        except Exception as e:
            click.echo(t("download_fail_get_ids", err=e))
            return

    # Filter out placeholder/example IDs
    invalid_ids = {"0000000000"}
    valid_book_ids = [bid for bid in book_ids if bid not in invalid_ids]

    if not book_ids:
        click.echo(t("download_no_ids"))
        return

    if not valid_book_ids:
        click.echo(t("download_only_example", example="0000000000"))
        click.echo(t("download_edit_config"))
        return

    # Initialize the requester, parser, saver, and downloader components
    curr_requester = get_requester(site, requester_cfg)
    curr_parser = get_parser(site, parser_cfg)
    curr_saver = get_saver(site, saver_cfg)
    setup_logging()
    curr_downloader = get_downloader(
        requester=curr_requester,
        parser=curr_parser,
        saver=curr_saver,
        site=site,
        config=downloader_cfg,
    )

    # Perform the download for each valid book ID
    for book_id in book_ids:
        click.echo(t("download_downloading", book_id=book_id, site=site))
        curr_downloader.download_one(book_id)

    # Prompt for parsing and wait for user input before shutting down
    if requester_cfg.auto_close:
        input(t("download_prompt_parse"))
        curr_requester.shutdown()
