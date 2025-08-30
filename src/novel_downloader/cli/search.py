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
from novel_downloader.core import search
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
        "--limit", "-l", type=int, default=20, metavar="N", help=t("search_limit_help")
    )
    parser.add_argument(
        "--site-limit",
        type=int,
        default=5,
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
    sites: Sequence[str] | None = args.site or None
    keyword: str = args.keyword
    overall_limit = max(1, args.limit)
    per_site_limit = max(1, args.site_limit)
    timeout = max(0.1, float(args.timeout))
    config_path: Path | None = Path(args.config) if args.config else None

    try:
        config_data = load_config(config_path)
    except Exception as e:
        ui.error(t("download_config_load_fail", err=str(e)))
        return

    async def _run() -> None:
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


def _prompt_user_select(results: Sequence[SearchResult]) -> SearchResult | None:
    """
    Show a Rich table of results and ask the user to pick one by index.

    :param results: A sequence of SearchResult dicts.
    :return: The chosen SearchResult, or None if cancelled/no results.
    """
    if not results:
        ui.warn(t("no_results"))
        return None

    columns = ["#", "Title", "Author", "Latest", "Updated", "Site", "Book ID"]
    rows = []
    for i, r in enumerate(results, 1):
        rows.append(
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
    ui.render_table("Search Results", columns, rows)

    idx = ui.select_index(t("prompt_select_index"), len(results))
    if idx is None:
        return None
    return results[idx - 1]
