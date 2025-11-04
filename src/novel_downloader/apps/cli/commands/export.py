#!/usr/bin/env python3
"""
novel_downloader.apps.cli.commands.export
-----------------------------------------

"""

from argparse import ArgumentParser, Namespace
from pathlib import Path

from novel_downloader.apps.cli import prompts, ui
from novel_downloader.apps.constants import DOWNLOAD_SUPPORT_SITES
from novel_downloader.apps.utils import load_or_init_config
from novel_downloader.infra.config import ConfigAdapter
from novel_downloader.infra.i18n import t
from novel_downloader.plugins import registrar
from novel_downloader.schemas import BookConfig

from ..ui_adapters import CLIExportUI
from .base import Command


class ExportCmd(Command):
    name = "export"
    help = t("Export previously downloaded novels.")

    @classmethod
    def add_arguments(cls, parser: ArgumentParser) -> None:
        parser.add_argument(
            "book_ids",
            nargs="*",
            help=t("Book ID(s) to export (optional; choose interactively if omitted)"),
        )
        parser.add_argument(
            "--format",
            nargs="+",
            help=t("Output format(s) (default: config)"),
        )
        parser.add_argument(
            "--site",
            help=t("Source site key (optional; choose interactively if omitted)"),
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
            "--stage",
            type=str,
            help=t("Export stage (e.g. raw, cleaner). Defaults to last stage."),
        )

    @classmethod
    def run(cls, args: Namespace) -> None:
        site: str | None = args.site
        stage: str | None = args.stage
        book_ids: list[str] = list(args.book_ids or [])
        config_path: Path | None = Path(args.config) if args.config else None
        formats: list[str] | None = args.format

        config_data = load_or_init_config(config_path)
        if config_data is None:
            return

        raw_cfg = config_data.get("general") or {}
        raw_dir = Path(raw_cfg.get("raw_data_dir", "./raw_data"))

        # site selection
        if not site:
            book_ids = []  # ignore passed-in ids when site is not specified
            site = prompts.select_site(raw_dir)
            if site is None:
                ui.warn(t("No site selected."))
                return

        ui.info(
            t("Using site: {site}").format(
                site=DOWNLOAD_SUPPORT_SITES.get(site, site),
            )
        )

        # book selection
        if not book_ids:
            selected = prompts.select_books(raw_dir, site)
            if not selected:
                ui.warn(t("No books selected."))
                return
            book_ids = selected

        adapter = ConfigAdapter(config=config_data)
        ui.setup_logging(console_level=adapter.get_log_level())

        plugins_cfg = adapter.get_plugins_config()
        if plugins_cfg.get("enable_local_plugins"):
            registrar.enable_local_plugins(
                plugins_cfg.get("local_plugins_path"),
                override=plugins_cfg.get("override_builtins", False),
            )

        formats = formats or adapter.get_export_fmt(site)
        books = cls._parse_book_args(book_ids, args.start, args.end)

        client = registrar.get_client(site, adapter.get_client_config(site))

        export_ui = CLIExportUI()

        for book in books:
            client.export(
                book,
                cfg=adapter.get_exporter_config(site),
                formats=formats,
                stage=stage,
                ui=export_ui,
            )

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
