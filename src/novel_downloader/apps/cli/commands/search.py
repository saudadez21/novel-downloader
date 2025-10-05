#!/usr/bin/env python3
"""
novel_downloader.apps.cli.commands.search
-----------------------------------------

"""

from argparse import ArgumentParser, Namespace
from collections.abc import Sequence
from pathlib import Path

from novel_downloader.apps.cli import ui
from novel_downloader.apps.constants import SEARCH_SUPPORT_SITES
from novel_downloader.infra.config import ConfigAdapter
from novel_downloader.infra.i18n import t
from novel_downloader.schemas import BookConfig, SearchResult

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
        from novel_downloader.usecases.config import load_or_init_config

        from ..ui_adapters import (
            CLIConfigUI,
            CLIDownloadUI,
            CLIExportUI,
            CLILoginUI,
            CLIProcessUI,
        )

        sites: Sequence[str] | None = args.site or None
        keyword: str = args.keyword
        overall_limit = None if args.limit is None else max(1, args.limit)
        per_site_limit = max(1, args.site_limit)
        timeout = max(0.1, float(args.timeout))
        config_path: Path | None = Path(args.config) if args.config else None

        config_data = load_or_init_config(config_path, CLIConfigUI())
        if config_data is None:
            return

        async def _run() -> None:
            from novel_downloader.usecases.search import search

            with ui.status(t("Searching for '{keyword}'...").format(keyword=keyword)):
                results = await search(
                    keyword=keyword,
                    sites=sites,
                    limit=overall_limit,
                    per_site_limit=per_site_limit,
                    timeout=timeout,
                )

            chosen = cls._prompt_user_select(results)
            if chosen is None:
                return

            site = chosen["site"]
            adapter = ConfigAdapter(config=config_data)
            books: list[BookConfig] = [BookConfig(book_id=chosen["book_id"])]

            log_level = adapter.get_log_level()
            ui.setup_logging(console_level=log_level)

            from novel_downloader.usecases.download import download_books

            login_ui = CLILoginUI()
            download_ui = CLIDownloadUI()
            await download_books(
                chosen["site"],
                books,
                adapter.get_downloader_config(site),
                adapter.get_fetcher_config(site),
                adapter.get_parser_config(site),
                login_ui=login_ui,
                download_ui=download_ui,
                login_config=adapter.get_login_config(site),
            )
            if not download_ui.completed_books:
                return

            # export
            from novel_downloader.usecases.export import export_books
            from novel_downloader.usecases.process import process_books

            process_books(
                site,
                list(download_ui.completed_books),
                adapter.get_pipeline_config(site),
                ui=CLIProcessUI(),
            )
            export_books(
                site=chosen["site"],
                books=list(download_ui.completed_books),
                exporter_cfg=adapter.get_exporter_config(site),
                export_ui=CLIExportUI(),
            )

        import asyncio

        asyncio.run(_run())

    @staticmethod
    def _prompt_user_select(
        results: Sequence[SearchResult],
        per_page: int = 10,
    ) -> SearchResult | None:
        """
        Show results in pages and let user select by global index.
        """
        if not results:
            ui.warn(t("No results found."))
            return None

        total = len(results)
        total_pages = max(1, (total + per_page - 1) // per_page)
        page = 1

        columns = [
            t("#"),
            t("Title"),
            t("Author"),
            t("Latest"),
            t("Updated"),
            t("Site Name"),
            t("Book ID"),
        ]
        all_rows = [
            [
                str(i),
                r["title"],
                r["author"],
                r["latest_chapter"],
                r["update_date"],
                SEARCH_SUPPORT_SITES.get(r["site"], r["site"]),
                r["book_id"],
            ]
            for i, r in enumerate(results, 1)
        ]

        while True:
            start = (page - 1) * per_page + 1
            end = min(page * per_page, total)

            page_rows = all_rows[start - 1 : end]

            ui.render_table(
                t("Search Results · Page {page}/{total_pages}").format(
                    page=page, total_pages=total_pages
                ),
                columns,
                page_rows,
            )

            numeric_choices = [str(i) for i in range(start, end + 1)]
            nav_choices = []
            if page < total_pages:
                nav_choices.append("n")
            if page > 1:
                nav_choices.append("p")

            choice = ui.prompt_choice(
                t(
                    "Enter a number, 'n' for next, 'p' for previous (press Enter to cancel)"  # noqa: E501
                ),
                numeric_choices + nav_choices,
            )

            if choice == "":
                return None  # cancel
            if choice == "n" and page < total_pages:
                page += 1
                continue
            if choice == "p" and page > 1:
                page -= 1
                continue
            if choice in numeric_choices:
                idx = int(choice)
                return results[idx - 1]
