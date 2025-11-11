#!/usr/bin/env python3
"""
novel_downloader.apps.cli.interactive
-------------------------------------

An interactive CLI mode for novel_downloader.

Provides a guided workflow for:
  1. Searching for novels
  2. Downloading novels (by URL or by site/book ID)
  3. Exporting downloaded novels
"""

import asyncio
from pathlib import Path

from novel_downloader.apps.cli import prompts, ui
from novel_downloader.apps.utils import load_or_init_config
from novel_downloader.infra.book_url_resolver import resolve_book_url
from novel_downloader.infra.config import ConfigAdapter
from novel_downloader.infra.i18n import t
from novel_downloader.plugins import registrar
from novel_downloader.plugins.search import search
from novel_downloader.schemas import BookConfig

from .ui_adapters import (
    CLIDownloadUI,
    CLIExportUI,
    CLILoginUI,
    CLIProcessUI,
)


def start_interactive() -> None:
    """Entry point for interactive mode."""
    ui.info(t("Starting interactive mode..."))

    config_data = load_or_init_config()
    if config_data is None:
        return

    adapter = ConfigAdapter(config=config_data)
    ui.setup_logging(console_level=adapter.get_log_level())

    plugins_cfg = adapter.get_plugins_config()
    if plugins_cfg.get("enable_local_plugins"):
        registrar.enable_local_plugins(
            plugins_cfg.get("local_plugins_path"),
            override=plugins_cfg.get("override_builtins", False),
        )

    while True:
        choice = prompts.select_main_action()
        if choice == "":
            ui.info(t("Goodbye!"))
            break

        if choice == "1":
            asyncio.run(_interactive_search(adapter))
        elif choice == "2":
            asyncio.run(_interactive_download(adapter))
        elif choice == "3":
            _interactive_export(adapter)
        else:
            ui.warn(t("Invalid choice. Please try again."))


async def _interactive_search(adapter: ConfigAdapter) -> None:
    """Search for a book across supported sites and optionally download it."""
    keyword = ui.prompt(t("Enter a keyword to search"))
    if not keyword:
        ui.warn(t("No keyword entered."))
        return

    with ui.status(t("Searching for '{keyword}'...").format(keyword=keyword)):
        try:
            results = await search(keyword=keyword)
        except Exception as e:
            ui.error(t("Search failed: {err}").format(err=e))
            return

    chosen = prompts.select_search_result(results)
    if chosen is None:
        ui.warn(t("Cancelled."))
        return

    site = chosen["site"]
    book = BookConfig(book_id=chosen["book_id"])

    if ui.confirm(t("Do you want to download this book now?"), default=True):
        await _do_download(adapter, site, book)


async def _interactive_download(adapter: ConfigAdapter) -> None:
    """Download a book directly by URL or Site/Book ID."""
    ui.info(t("Download Mode"))

    mode = ui.prompt_choice(
        t("Enter 'u' for URL or 'i' for Site + Book ID (Enter to cancel)"),
        ["u", "i", ""],
    )
    if mode == "":
        ui.warn(t("Cancelled."))
        return

    if mode == "u":
        url = ui.prompt(t("Enter the book URL"))
        if not url:
            ui.warn(t("No URL provided."))
            return
        info = resolve_book_url(url)
        if not info:
            ui.error(t("Failed to recognize or parse the provided URL."))
            return

        book_id = info.get("book_id")
        site = info.get("site_key")

        if not book_id:
            ui.error(t("The provided URL does not contain a valid book ID."))
            return

        book = BookConfig(book_id=book_id)
    else:
        site = ui.prompt(t("Enter site key"))
        book_id = ui.prompt(t("Enter book ID"))
        if not site or not book_id:
            ui.warn(t("Incomplete information."))
            return
        book = BookConfig(book_id=book_id)

    if not site or not book:
        ui.error(t("Failed to initialize download parameters."))
        return

    await _do_download(adapter, site, book)


async def _do_download(adapter: ConfigAdapter, site: str, book: BookConfig) -> None:
    """Shared routine to handle login + download + process."""
    client = registrar.get_client(site, config=adapter.get_client_config(site))
    login_ui = CLILoginUI()
    download_ui = CLIDownloadUI()

    try:
        async with client:
            if adapter.get_login_required(site):
                success = await client.login(
                    ui=login_ui,
                    login_cfg=adapter.get_login_config(site),
                )
                if not success:
                    ui.warn(t("Login failed."))
                    return

            await client.download(book, ui=download_ui)

    except ValueError as e:
        ui.warn(
            t("'{site}' is currently not supported: {err}").format(site=site, err=e)
        )
        return
    except Exception as e:
        ui.error(
            t("Error while downloading from {site}: {err}").format(site=site, err=e)
        )
        return

    process_ui = CLIProcessUI()
    client.process(
        book,
        processors=adapter.get_processor_configs(site),
        ui=process_ui,
    )

    if ui.confirm(t("Do you want to export this book now?"), default=True):
        _interactive_export(adapter, site=site, book=book)


def _interactive_export(
    adapter: ConfigAdapter, site: str | None = None, book: BookConfig | None = None
) -> None:
    """Export novels interactively."""
    raw_cfg = adapter.get_config().get("general") or {}
    raw_dir = Path(raw_cfg.get("raw_data_dir", "./raw_data"))

    if not site:
        site = prompts.select_site(raw_dir)
        if not site:
            ui.warn(t("No site selected."))
            return

    if not book:
        book_ids = prompts.select_books(raw_dir, site)
        if not book_ids:
            ui.warn(t("No books selected."))
            return
        book = BookConfig(book_id=book_ids[0])

    formats = adapter.get_export_fmt(site)
    client = registrar.get_client(site)
    export_ui = CLIExportUI()

    ui.info(
        t("Exporting book '{book_id}' in formats: {fmt}").format(
            book_id=book.book_id, fmt=", ".join(formats)
        )
    )

    try:
        client.export(
            book,
            cfg=adapter.get_exporter_config(site),
            formats=formats,
            ui=export_ui,
        )
        ui.success(t("Export completed successfully."))
    except Exception as e:
        ui.error(t("Export failed: {err}").format(err=e))
