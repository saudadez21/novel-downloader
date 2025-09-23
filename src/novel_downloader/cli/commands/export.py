#!/usr/bin/env python3
"""
novel_downloader.cli.commands.export
------------------------------------

"""

from argparse import ArgumentParser, Namespace
from pathlib import Path

from novel_downloader.cli import ui
from novel_downloader.config import ConfigAdapter, copy_default_config, load_config
from novel_downloader.models import BookConfig
from novel_downloader.utils.i18n import t

from .base import Command


class ExportCmd(Command):
    name = "export"
    help = t("Export previously downloaded novels.")

    @classmethod
    def add_arguments(cls, parser: ArgumentParser) -> None:
        parser.add_argument(
            "book_ids",
            nargs="+",
            help=t("Book ID(s) to export"),
        )
        parser.add_argument(
            "--format",
            choices=["txt", "epub"],
            nargs="+",
            help=t("Output format(s) (default: config)"),
        )
        parser.add_argument(
            "--site",
            default="qidian",
            help=t("Source site key (default: {default})").format(default="qidian"),
        )
        parser.add_argument(
            "--config", type=str, help=t("Path to the configuration file")
        )

    @classmethod
    def run(cls, args: Namespace) -> None:
        from novel_downloader.cli.services.export import export_books

        site: str = args.site
        config_path: Path | None = Path(args.config) if args.config else None
        formats: list[str] | None = args.format

        ui.info(t("Using site: {site}").format(site=site))
        try:
            config_data = load_config(config_path)
        except FileNotFoundError:
            if config_path is None:
                config_path = Path("settings.toml")
            copy_default_config(config_path)
            ui.warn(
                t("No config found; created at {path}.").format(
                    path=str(config_path.resolve())
                )
            )
            return
        except ValueError as e:
            ui.error(t("Failed to load configuration: {err}").format(err=str(e)))
            return

        adapter = ConfigAdapter(config=config_data, site=site)

        log_level = adapter.get_log_level()
        ui.setup_logging(console_level=log_level)

        books: list[BookConfig] = [{"book_id": bid} for bid in args.book_ids]

        export_books(
            site=site,
            books=books,
            exporter_cfg=adapter.get_exporter_config(),
            formats=formats,
        )
