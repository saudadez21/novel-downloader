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
    help = t("help_download")

    @classmethod
    def add_arguments(cls, parser: ArgumentParser) -> None:
        parser.add_argument("book_ids", nargs="*", help=t("download_book_ids"))
        parser.add_argument("--site", help=t("download_option_site"))
        parser.add_argument("--config", type=str, help=t("help_config"))
        parser.add_argument("--start", type=str, help=t("download_option_start"))
        parser.add_argument("--end", type=str, help=t("download_option_end"))
        parser.add_argument(
            "--no-export",
            action="store_true",
            help=t("download_option_no_export"),
        )

    @classmethod
    def run(cls, args: Namespace) -> None:
        config_path: Path | None = Path(args.config) if args.config else None
        site: str | None = args.site

        # book_ids
        if site:  # SITE MODE
            book_ids = cls._parse_book_args(args.book_ids, args.start, args.end)
        else:  # URL MODE
            from novel_downloader.utils.book_url_resolver import resolve_book_url

            ui.info(t("download_url_mode"))
            if len(args.book_ids) != 1:
                ui.error(t("download_url_expected", n=len(args.book_ids)))
                return

            raw_url = args.book_ids[0]
            resolved = resolve_book_url(raw_url)
            if not resolved:
                ui.error(t("download_url_parse_fail", url=raw_url))
                return

            site = resolved["site_key"]
            first: BookConfig = {"book_id": resolved["book"]["book_id"]}
            if args.start:
                first["start_id"] = args.start
            if args.end:
                first["end_id"] = args.end
            book_ids = [first]
            ui.info(t("download_resolved", site=site, book_id=first["book_id"]))

        ui.info(t("download_site_info", site=site))
        try:
            config_data = load_config(config_path)
        except FileNotFoundError:
            if config_path is None:
                config_path = Path("settings.toml")
            copy_default_config(config_path)
            ui.warn(t("config_initialized", path=str(config_path.resolve())))
            return
        except ValueError as e:
            ui.error(t("download_config_load_fail", err=str(e)))
            return
        adapter = ConfigAdapter(config=config_data, site=site)

        if not book_ids and args.site:
            try:
                book_ids = adapter.get_book_ids()
            except Exception as e:
                ui.error(t("download_fail_get_ids", err=str(e)))
                return

        if not book_ids:
            ui.warn(t("download_no_ids"))
            return

        # logging
        log_level = adapter.get_log_level()
        ui.setup_logging(console_level=log_level)

        # download
        import asyncio

        from novel_downloader.cli.services.download import download_books

        asyncio.run(
            download_books(
                site,
                book_ids,
                adapter.get_downloader_config(),
                adapter.get_fetcher_config(),
                adapter.get_parser_config(),
                adapter.get_login_config(),
            )
        )

        # export
        if not args.no_export:
            from novel_downloader.cli.services.export import export_books

            export_books(site, book_ids, adapter.get_exporter_config())
        else:
            ui.info(t("download_export_skipped"))

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
