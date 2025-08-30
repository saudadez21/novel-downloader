#!/usr/bin/env python3
"""
novel_downloader.cli.export
---------------------------

Export existing books into TXT/EPUB formats.
"""

from __future__ import annotations

from argparse import Namespace, _SubParsersAction
from pathlib import Path

from novel_downloader.cli import ui
from novel_downloader.config import ConfigAdapter, load_config
from novel_downloader.core import get_exporter
from novel_downloader.utils.i18n import t
from novel_downloader.utils.logger import setup_logging


def register_export_subcommand(subparsers: _SubParsersAction) -> None:  # type: ignore
    """Register the `export` subcommand and its options."""
    parser = subparsers.add_parser("export", help=t("help_export"))

    parser.add_argument("book_ids", nargs="+", help=t("download_book_ids"))
    parser.add_argument(
        "--format",
        choices=["txt", "epub", "all"],
        default="all",
        help=t("export_format_help"),
    )
    parser.add_argument(
        "--site", default="qidian", help=t("download_option_site", default="qidian")
    )
    parser.add_argument("--config", type=str, help=t("help_config"))

    parser.set_defaults(func=handle_export)


def handle_export(args: Namespace) -> None:
    """Handle the `export` subcommand."""
    site: str = args.site
    config_path: Path | None = Path(args.config) if args.config else None
    book_ids: list[str] = args.book_ids
    export_format: str = args.format

    ui.info(t("download_site_info", site=site))

    try:
        config_data = load_config(config_path)
    except Exception as e:
        ui.error(t("download_config_load_fail", err=str(e)))
        return

    adapter = ConfigAdapter(config=config_data, site=site)
    exporter_cfg = adapter.get_exporter_config()
    log_level = adapter.get_log_level()
    exporter = get_exporter(site, exporter_cfg)
    setup_logging(log_level=log_level)

    for book_id in book_ids:
        ui.info(t("export_processing", book_id=book_id, format=export_format))

        if export_format in {"txt", "all"}:
            try:
                exporter.export_as_txt(book_id)
                ui.success(t("export_success_txt", book_id=book_id))
            except Exception as e:
                ui.error(t("export_failed_txt", book_id=book_id, err=str(e)))

        if export_format in {"epub", "all"}:
            try:
                exporter.export_as_epub(book_id)
                ui.success(t("export_success_epub", book_id=book_id))
            except Exception as e:
                ui.error(t("export_failed_epub", book_id=book_id, err=str(e)))
