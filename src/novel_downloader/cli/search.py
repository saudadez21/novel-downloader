#!/usr/bin/env python3
"""
novel_downloader.cli.search
---------------------------

"""

import asyncio
from argparse import Namespace, _SubParsersAction
from collections.abc import Sequence
from pathlib import Path

from novel_downloader.cli.download import _download
from novel_downloader.config import ConfigAdapter, load_config
from novel_downloader.core import search
from novel_downloader.models import BookConfig, SearchResult
from novel_downloader.utils.i18n import t


def register_search_subcommand(subparsers: _SubParsersAction) -> None:  # type: ignore
    parser = subparsers.add_parser("search", help=t("help_search"))

    parser.add_argument(
        "--site",
        "-s",
        action="append",
        metavar="SITE",
        help=t("help_search_sites"),
    )
    parser.add_argument(
        "keyword",
        help=t("help_search_keyword"),
    )
    parser.add_argument(
        "--config",
        type=str,
        help=t("help_config"),
    )

    parser.set_defaults(func=handle_search)


def handle_search(args: Namespace) -> None:
    """
    Handler for the `search` subcommand. Loads config, runs the search,
    prompts the user to pick one result, then kicks off download.
    """
    sites: Sequence[str] | None = args.site or None
    keyword: str = args.keyword
    config_path: Path | None = Path(args.config) if args.config else None

    try:
        config_data = load_config(config_path)
    except Exception as e:
        print(t("download_config_load_fail", err=str(e)))
        return

    results = search(
        keyword=keyword,
        sites=sites,
        limit=10,
    )

    chosen = _prompt_user_select(results)
    if chosen is None:
        # user cancelled or no valid choice
        return

    adapter = ConfigAdapter(config=config_data, site=chosen["site"])
    books: list[BookConfig] = [{"book_id": chosen["book_id"]}]
    asyncio.run(_download(adapter, chosen["site"], books))


def _prompt_user_select(
    results: Sequence[SearchResult],
    max_attempts: int = 3,
) -> SearchResult | None:
    """
    Display a numbered list of results and prompt the user to pick one.

    :param results:      A list of SearchResult dicts.
    :param max_attempts: How many bad inputs to tolerate before giving up.
    :return:             The chosen SearchResult, or None if cancelled/failed.
    """
    if not results:
        print(t("no_results"))
        return None

    # Show choices
    for i, r in enumerate(results, start=1):
        print(f"[{i}] {r['title']} - {r['author']} ({r['site']})")

    attempts = 0
    while attempts < max_attempts:
        choice = input(t("prompt_select_index")).strip()
        if choice == "":
            return None
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(results):
                return results[idx - 1]
        print(t("invalid_selection"))
        attempts += 1

    return None
