#!/usr/bin/env python3
"""
novel_downloader.cli.commands.download
--------------------------------------

"""

from argparse import ArgumentParser, Namespace
from pathlib import Path

from novel_downloader.cli import ui
from novel_downloader.config import ConfigAdapter, copy_default_config, load_config
from novel_downloader.models import BookConfig
from novel_downloader.utils.i18n import t

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
        config_path: Path | None = Path(args.config) if args.config else None
        site: str | None = args.site

        # book_ids
        if site:  # SITE MODE
            books = cls._parse_book_args(args.book_ids, args.start, args.end)
        else:  # URL MODE
            from novel_downloader.utils.book_url_resolver import resolve_book_url

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
            first: BookConfig = {"book_id": resolved["book"]["book_id"]}
            if args.start:
                first["start_id"] = args.start
            if args.end:
                first["end_id"] = args.end
            books = [first]
            ui.info(
                t("Resolved URL to site '{site}' with book ID '{book_id}'.").format(
                    site=site, book_id=first["book_id"]
                )
            )

        ui.info(t("Using site: {site}").format(site=site))
        try:
            config_data = load_config(config_path)
        except FileNotFoundError:
            if config_path is None:
                config_path = Path("settings.toml")
            ui.warn(
                t("No config found at {path}.").format(path=str(config_path.resolve()))
            )
            if ui.confirm(
                t("Would you like to create a default config?"), default=True
            ):
                copy_default_config(config_path)
                ui.success(
                    t("Created default config at {path}.").format(
                        path=str(config_path.resolve())
                    )
                )
            else:
                ui.error(t("Cannot continue without a config file."))
            return
        except ValueError as e:
            ui.error(t("Failed to load configuration: {err}").format(err=str(e)))
            return
        adapter = ConfigAdapter(config=config_data, site=site)

        if not books and args.site:
            try:
                books = adapter.get_book_ids()
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

        # download
        import asyncio

        from novel_downloader.cli.services.download import download_books

        success = asyncio.run(
            download_books(
                site,
                books,
                adapter.get_downloader_config(),
                adapter.get_fetcher_config(),
                adapter.get_parser_config(),
                adapter.get_login_config(),
            )
        )
        if not success:
            return

        # export
        if not args.no_export:
            from novel_downloader.cli.services.export import export_books

            export_books(site, books, adapter.get_exporter_config())
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
        first: BookConfig = {"book_id": book_ids[0]}
        if start_id:
            first["start_id"] = start_id
        if end_id:
            first["end_id"] = end_id
        result.append(first)

        for book_id in book_ids[1:]:
            result.append({"book_id": book_id})

        return result
