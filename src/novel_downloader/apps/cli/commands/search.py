#!/usr/bin/env python3
"""
novel_downloader.apps.cli.commands.search
-----------------------------------------

"""

from argparse import ArgumentParser, Namespace
from collections.abc import Sequence
from pathlib import Path

from novel_downloader.apps.cli import prompts, ui
from novel_downloader.apps.utils import load_or_init_config
from novel_downloader.infra.config import ConfigAdapter
from novel_downloader.infra.i18n import t
from novel_downloader.plugins import registrar
from novel_downloader.schemas import BookConfig

from ..ui_adapters import (
    CLIDownloadUI,
    CLIExportUI,
    CLILoginUI,
    CLIProcessUI,
)
from .base import Command


class SearchCmd(Command):
    name = "search"
    help = t("Search for books across one or more sites.")

    @classmethod
    def add_arguments(cls, parser: ArgumentParser) -> None:
        parser.add_argument(
            "--site",
            "-s",
            action="append",
            metavar="SITE",
            help=t("Restrict search to specific site key(s). Default: all sites."),
        )
        parser.add_argument("keyword", help=t("Search keyword"))
        parser.add_argument(
            "--config", type=str, help=t("Path to the configuration file")
        )
        parser.add_argument(
            "--limit",
            "-l",
            type=int,
            default=None,
            metavar="N",
            help=t("Maximum number of total results"),
        )
        parser.add_argument(
            "--site-limit",
            type=int,
            default=10,
            metavar="M",
            help=t("Maximum number of results per site (default: 10)"),
        )
        parser.add_argument(
            "--timeout",
            type=float,
            default=5.0,
            metavar="SECS",
            help=t("Request timeout in seconds (default: 5.0)"),
        )

    @classmethod
    def run(cls, args: Namespace) -> None:
        sites: Sequence[str] | None = args.site or None
        keyword: str = args.keyword
        overall_limit = None if args.limit is None else max(1, args.limit)
        per_site_limit = max(1, args.site_limit)
        timeout = max(0.1, float(args.timeout))
        config_path: Path | None = Path(args.config) if args.config else None

        config_data = load_or_init_config(config_path)
        if config_data is None:
            return
        adapter = ConfigAdapter(config=config_data)
        ui.setup_logging(console_level=adapter.get_log_level())

        async def _run() -> None:
            from novel_downloader.plugins.search import search

            with ui.status(t("Searching for '{keyword}'...").format(keyword=keyword)):
                results = await search(
                    keyword=keyword,
                    sites=sites,
                    limit=overall_limit,
                    per_site_limit=per_site_limit,
                    timeout=timeout,
                )

            chosen = prompts.select_search_result(results)
            if chosen is None:
                return

            site = chosen["site"]
            books: list[BookConfig] = [BookConfig(book_id=chosen["book_id"])]

            login_ui = CLILoginUI()
            download_ui = CLIDownloadUI()
            client = registrar.get_client(site, adapter.get_client_config(site))

            try:
                async with client:
                    if adapter.get_login_required(site):
                        succ = await client.login(
                            ui=login_ui,
                            login_cfg=adapter.get_login_config(site),
                        )
                        if not succ:
                            return

                    for book in books:
                        await client.download(book, ui=download_ui)
            except ValueError as e:
                ui.warn(
                    t("'{site}' is currently not supported: {err}").format(
                        site=site, err=e
                    )
                )
                return
            except Exception as e:
                ui.error(t("Site error ({site}): {err}").format(site=site, err=e))
                return

            if not download_ui.completed_books:
                return

            process_ui = CLIProcessUI()
            export_ui = CLIExportUI()

            for book in download_ui.completed_books:
                client.process(
                    book,
                    processors=adapter.get_processor_configs(site),
                    ui=process_ui,
                )
                client.export(
                    book,
                    cfg=adapter.get_exporter_config(site),
                    formats=args.format or adapter.get_export_fmt(site),
                    ui=export_ui,
                )

        import asyncio

        asyncio.run(_run())
