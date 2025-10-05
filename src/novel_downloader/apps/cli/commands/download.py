#!/usr/bin/env python3
"""
novel_downloader.apps.cli.commands.download
-------------------------------------------

"""

from argparse import ArgumentParser, Namespace
from pathlib import Path

from novel_downloader.apps.cli import ui
from novel_downloader.infra.config import ConfigAdapter
from novel_downloader.infra.i18n import t
from novel_downloader.schemas import BookConfig

from .base import Command


class DownloadCmd(Command):
    name = "download"
    help = t("Download novels by book ID or URL.")

    @classmethod
    def add_arguments(cls, parser: ArgumentParser) -> None:
        parser.add_argument(
            "book_ids", nargs="*", help=t("Book ID(s) or URL to download")
        )
        parser.add_argument(
            "--site",
            help=t("Source site key (auto-detected if omitted and URL is provided)"),
        )
        parser.add_argument(
            "--config", type=str, help=t("Path to the configuration file")
        )
        parser.add_argument(
            "--start",
            type=str,
            help=t("Start chapter ID (applies only to the first book)"),
        )
        parser.add_argument(
            "--end",
            type=str,
            help=t("End chapter ID (applies only to the first book)"),
        )
        parser.add_argument(
            "--no-export",
            action="store_true",
            help=t("Skip export step (download only)"),
        )

    @classmethod
    def run(cls, args: Namespace) -> None:
        from novel_downloader.usecases.config import load_or_init_config

        from ..ui_adapters import (
            CLIConfigUI,
            CLIDownloadUI,
            CLIExportUI,
            CLILoginUI,
            CLIProcessUI,
        )

        config_path: Path | None = Path(args.config) if args.config else None
        site: str | None = args.site

        # book_ids
        if site:  # SITE MODE
            books = cls._parse_book_args(args.book_ids, args.start, args.end)
        else:  # URL MODE
            from novel_downloader.libs.book_url_resolver import resolve_book_url

            ui.info(t("No --site provided; detecting site from URL..."))
            if len(args.book_ids) != 1:
                ui.error(
                    t(
                        "Expected exactly one URL argument when --site is omitted (got {n})."  # noqa: E501
                    ).format(n=len(args.book_ids))
                )
                return

            raw_url = args.book_ids[0]
            resolved = resolve_book_url(raw_url)
            if not resolved:
                ui.error(
                    t("Could not resolve site and book from URL: {url}").format(
                        url=raw_url
                    )
                )
                return

            site = resolved["site_key"]
            first = BookConfig(
                book_id=resolved["book"].book_id,
                start_id=args.start,
                end_id=args.end,
            )
            books = [first]
            ui.info(
                t("Resolved URL to site '{site}' with book ID '{book_id}'.").format(
                    site=site, book_id=first.book_id
                )
            )

        config_data = load_or_init_config(config_path, CLIConfigUI())
        if config_data is None:
            return

        ui.info(t("Using site: {site}").format(site=site))
        adapter = ConfigAdapter(config=config_data)

        if not books and args.site:
            try:
                books = adapter.get_book_ids(site)
            except Exception as e:
                ui.error(
                    t("Failed to read book IDs from configuration: {err}").format(
                        err=str(e)
                    )
                )
                return

        if not books:
            ui.warn(t("No book IDs provided. Exiting."))
            return

        log_level = adapter.get_log_level()
        ui.setup_logging(console_level=log_level)

        plugins_cfg = adapter.get_plugins_config()
        if plugins_cfg.get("enable_local_plugins"):
            from novel_downloader.plugins.registry import registrar

            registrar.enable_local_plugins(
                plugins_cfg.get("local_plugins_path"),
                override=plugins_cfg.get("override_builtins", False),
            )

        # download
        import asyncio

        from novel_downloader.usecases.download import download_books

        login_ui = CLILoginUI()
        download_ui = CLIDownloadUI()

        asyncio.run(
            download_books(
                site,
                books,
                adapter.get_downloader_config(site),
                adapter.get_fetcher_config(site),
                adapter.get_parser_config(site),
                login_ui=login_ui,
                download_ui=download_ui,
                login_config=adapter.get_login_config(site),
            )
        )
        if not download_ui.completed_books:
            return

        # export
        if not args.no_export:
            from novel_downloader.usecases.export import export_books
            from novel_downloader.usecases.process import process_books

            process_books(
                site,
                list(download_ui.completed_books),
                adapter.get_pipeline_config(site),
                ui=CLIProcessUI(),
            )
            export_books(
                site,
                list(download_ui.completed_books),
                adapter.get_exporter_config(site),
                export_ui=CLIExportUI(),
            )
        else:
            ui.info(t("Export skipped (--no-export)"))

    @staticmethod
    def _parse_book_args(
        book_ids: list[str],
        start_id: str | None,
        end_id: str | None,
    ) -> list[BookConfig]:
        """
        Convert CLI arguments into a list of `BookConfig`.
        """
        if not book_ids:
            return []

        result: list[BookConfig] = []
        result.append(
            BookConfig(
                book_id=book_ids[0],
                start_id=start_id,
                end_id=end_id,
            )
        )

        for book_id in book_ids[1:]:
            result.append(BookConfig(book_id=book_id))

        return result
