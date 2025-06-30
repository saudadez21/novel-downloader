#!/usr/bin/env python3
"""
novel_downloader.cli.export
---------------------------

"""

from argparse import Namespace, _SubParsersAction
from pathlib import Path

from novel_downloader.config import ConfigAdapter, load_config
from novel_downloader.core.factory import get_exporter
from novel_downloader.utils.i18n import t


def register_export_subcommand(subparsers: _SubParsersAction) -> None:  # type: ignore
    parser = subparsers.add_parser("export", help=t("help_export"))

    parser.add_argument(
        "book_ids",
        nargs="+",
        help=t("download_book_ids"),
    )
    parser.add_argument(
        "--format",
        choices=["txt", "epub", "all"],
        default="all",
        help=t("export_format_help"),
    )
    parser.add_argument(
        "--site",
        default="qidian",
        help=t("download_option_site", default="qidian"),
    )
    parser.add_argument(
        "--config",
        type=str,
        help=t("help_config"),
    )

    parser.set_defaults(func=handle_export)


def handle_export(args: Namespace) -> None:
    site: str = args.site
    config_path: Path | None = Path(args.config) if args.config else None
    book_ids: list[str] = args.book_ids
    export_format: str = args.format

    print(t("download_site_info", site=site))

    try:
        config_data = load_config(config_path)
    except Exception as e:
        print(t("download_config_load_fail", err=str(e)))
        return

    adapter = ConfigAdapter(config=config_data, site=site)
    exporter_cfg = adapter.get_exporter_config()
    exporter = get_exporter(site, exporter_cfg)

    for book_id in book_ids:
        print(t("export_processing", book_id=book_id, format=export_format))

        if export_format in {"txt", "all"}:
            try:
                exporter.export_as_txt(book_id)
                print(t("export_success_txt", book_id=book_id))
            except Exception as e:
                print(t("export_failed_txt", book_id=book_id, err=str(e)))

        if export_format in {"epub", "all"}:
            try:
                exporter.export_as_epub(book_id)
                print(t("export_success_epub", book_id=book_id))
            except Exception as e:
                print(t("export_failed_epub", book_id=book_id, err=str(e)))
