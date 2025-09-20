#!/usr/bin/env python3
"""
novel_downloader.cli.search
---------------------------

Search across supported sites, let the user pick one result, then
hand off to the download flow.
"""

from __future__ import annotations

import asyncio
from argparse import Namespace, _SubParsersAction
from collections.abc import Sequence
from pathlib import Path

from novel_downloader.cli import ui
from novel_downloader.cli.download import _download
from novel_downloader.config import ConfigAdapter, load_config
from novel_downloader.models import BookConfig, SearchResult
from novel_downloader.utils.i18n import t


def register_search_subcommand(subparsers: _SubParsersAction) -> None:  # type: ignore
    """Register the `search` subcommand and its options."""
    parser = subparsers.add_parser("search", help=t("help_search"))

    parser.add_argument(
        "--site", "-s", action="append", metavar="SITE", help=t("search_sites_help")
    )
    parser.add_argument("keyword", help=t("search_keyword_help"))
    parser.add_argument("--config", type=str, help=t("help_config"))
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=None,
        metavar="N",
        help=t("search_limit_help"),
    )
    parser.add_argument(
        "--site-limit",
        type=int,
        default=10,
        metavar="M",
        help=t("search_site_limit_help"),
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        metavar="SECS",
        help=t("search_timeout_help", secs="5.0"),
    )

    parser.set_defaults(func=handle_search)


def handle_search(args: Namespace) -> None:
    """Handle the `search` subcommand."""
    from novel_downloader.core.searchers import search

    sites: Sequence[str] | None = args.site or None
    keyword: str = args.keyword
    overall_limit = None if args.limit is None else max(1, args.limit)
    per_site_limit = max(1, args.site_limit)
    timeout = max(0.1, float(args.timeout))
    config_path: Path | None = Path(args.config) if args.config else None

    try:
        config_data = load_config(config_path)
    except Exception as e:
        ui.error(t("download_config_load_fail", err=str(e)))
        return

    async def _run() -> None:
        with ui.status(
            t("searching", keyword=keyword, sites=", ".join(sites) if sites else "all")
        ):
            results = await search(
                keyword=keyword,
                sites=sites,
                limit=overall_limit,
                per_site_limit=per_site_limit,
                timeout=timeout,
            )

        chosen = _prompt_user_select(results)
        if chosen is None:
            return

        adapter = ConfigAdapter(config=config_data, site=chosen["site"])
        books: list[BookConfig] = [{"book_id": chosen["book_id"]}]
        await _download(adapter, chosen["site"], books)

    asyncio.run(_run())


def _prompt_user_select(
    results: Sequence[SearchResult],
    per_page: int = 10,
) -> SearchResult | None:
    """
    Show results in pages and let user select by global index.

    Navigation:
      * number: select that item
      * 'n': next page
      * 'p': previous page
      * Enter: cancel

    :param results: A sequence of SearchResult dicts.
    :return: The chosen SearchResult, or None if cancelled/no results.
    """
    if not results:
        ui.warn(t("no_results"))
        return None

    total = len(results)
    total_pages = max(1, (total + per_page - 1) // per_page)
    page = 1

    columns = [
        t("col_index"),
        t("col_title"),
        t("col_author"),
        t("col_latest"),
        t("col_updated"),
        t("col_site"),
        t("col_book_id"),
    ]
    all_rows = []
    for i, r in enumerate(results, 1):
        all_rows.append(
            [
                str(i),
                r["title"],
                r["author"],
                r["latest_chapter"],
                r["update_date"],
                r["site"],
                r["book_id"],
            ]
        )

    while True:
        start = (page - 1) * per_page + 1
        end = min(page * per_page, total)

        page_rows = all_rows[start - 1 : end]

        ui.render_table(
            t("page_status", page=page, total_pages=total_pages),
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
            t("prompt_select_index"),
            numeric_choices + nav_choices,
        )

        if choice == "":
            # Cancel
            return None
        if choice == "n" and page < total_pages:
            page += 1
            continue
        if choice == "p" and page > 1:
            page -= 1
            continue
        # Otherwise expect a number within the global range
        if choice in numeric_choices:
            idx = int(choice)
            return results[idx - 1]
