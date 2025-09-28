#!/usr/bin/env python3
"""
novel_downloader.apps.cli.commands.export
-----------------------------------------

"""

from argparse import ArgumentParser, Namespace
from pathlib import Path

from novel_downloader.apps.cli import ui
from novel_downloader.apps.constants import DOWNLOAD_SUPPORT_SITES
from novel_downloader.infra.config import ConfigAdapter
from novel_downloader.infra.i18n import t
from novel_downloader.schemas import BookConfig

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
            choices=["txt", "epub"],
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

    @classmethod
    def run(cls, args: Namespace) -> None:
        from ..handlers.config import load_or_init_config

        site: str | None = args.site
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
            site = cls._prompt_select_site(raw_dir)
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
            selected = cls._prompt_select_book_ids(raw_dir, site)
            if not selected:
                ui.warn(t("No books selected."))
                return
            book_ids = selected

        adapter = ConfigAdapter(config=config_data, site=site)
        ui.setup_logging(console_level=adapter.get_log_level())

        plugins_cfg = adapter.get_plugins_config()
        if plugins_cfg.get("enable_local_plugins"):
            from novel_downloader.plugins.registry import registrar

            registrar.enable_local_plugins(plugins_cfg.get("local_plugins_path"))

        books = cls._parse_book_args(book_ids, args.start, args.end)

        from ..handlers.export import export_books

        export_books(
            site=site,
            books=books,
            exporter_cfg=adapter.get_exporter_config(),
            formats=formats,
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
        first: BookConfig = {"book_id": book_ids[0]}
        if start_id:
            first["start_id"] = start_id
        if end_id:
            first["end_id"] = end_id
        result.append(first)

        for book_id in book_ids[1:]:
            result.append({"book_id": book_id})

        return result

    @staticmethod
    def _prompt_select_site(raw_dir: Path, per_page: int = 10) -> str | None:
        if not raw_dir.exists():
            ui.error(t("Raw data directory does not exist: {p}").format(p=str(raw_dir)))
            return None

        site_dirs = sorted([p for p in raw_dir.iterdir() if p.is_dir()])
        if not site_dirs:
            ui.warn(t("No sites found under {p}.").format(p=str(raw_dir)))
            return None

        all_rows = [
            [str(i), DOWNLOAD_SUPPORT_SITES.get(p.name, p.name), p.name]
            for i, p in enumerate(site_dirs, 1)
        ]

        total = len(all_rows)
        total_pages = max(1, (total + per_page - 1) // per_page)
        page = 1

        while True:
            start = (page - 1) * per_page + 1
            end = min(page * per_page, total)
            page_rows = all_rows[start - 1 : end]

            ui.render_table(
                t("Available Sites · Page {page}/{total}").format(
                    page=page, total=total_pages
                ),
                [t("#"), t("Site Name"), t("Site Key")],
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
                return None
            if choice == "n" and page < total_pages:
                page += 1
                continue
            if choice == "p" and page > 1:
                page -= 1
                continue
            if choice in numeric_choices:
                idx = int(choice)
                return site_dirs[idx - 1].name

    @staticmethod
    def _prompt_select_book_ids(
        raw_dir: Path, site: str, per_page: int = 10
    ) -> list[str]:
        import json

        site_dir = raw_dir / site
        if not site_dir.exists():
            ui.error(t("Site directory does not exist: {p}").format(p=str(site_dir)))
            return []

        book_dirs = sorted([p for p in site_dir.iterdir() if p.is_dir()])
        if not book_dirs:
            ui.warn(t("No books found under site '{site}'.").format(site=site))
            return []

        all_rows = []
        for i, p in enumerate(book_dirs, 1):
            book_id = p.name
            book_name, author = "", ""
            info_path = p / "book_info.json"
            if info_path.exists():
                try:
                    with info_path.open("r", encoding="utf-8") as f:
                        meta = json.load(f)
                        book_name = str(meta.get("book_name", "") or "")
                        author = str(meta.get("author", "") or "")
                except Exception:
                    ui.warn(t("Failed to read metadata for {bid}").format(bid=book_id))
            all_rows.append([str(i), book_id, book_name, author])

        total = len(all_rows)
        total_pages = max(1, (total + per_page - 1) // per_page)
        page = 1

        while True:
            start = (page - 1) * per_page + 1
            end = min(page * per_page, total)
            page_rows = all_rows[start - 1 : end]

            ui.render_table(
                t("Available Books for {site} · Page {page}/{total}").format(
                    site=site, page=page, total=total_pages
                ),
                [t("#"), t("Book ID"), t("Title"), t("Author")],
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
                    "Enter numbers (e.g. 1,3,5), 'a' for all, 'n' next, 'p' previous (Enter to cancel)"  # noqa: E501
                ),
                numeric_choices + nav_choices + ["a"],
            )

            if choice == "":
                return []
            if choice == "a":
                return [p.name for p in book_dirs]
            if choice == "n" and page < total_pages:
                page += 1
                continue
            if choice == "p" and page > 1:
                page -= 1
                continue
            if "," in choice or choice in numeric_choices:
                try:
                    idxs = sorted({int(s) for s in choice.split(",") if s.strip()})
                except ValueError:
                    ui.warn(t("Invalid input."))
                    continue
                if any(i < 1 or i > len(book_dirs) for i in idxs):
                    ui.warn(t("One or more indices out of range."))
                    continue
                return [book_dirs[i - 1].name for i in idxs]
