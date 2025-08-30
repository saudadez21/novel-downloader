#!/usr/bin/env python3
"""
novel_downloader.cli.search
---------------------------

"""

import asyncio
from argparse import Namespace, _SubParsersAction
from collections.abc import Sequence
from pathlib import Path

from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

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
    parser.add_argument(
        "--limit",
        "-l",
        type=int,
        default=20,
        metavar="N",
        help=t("help_search_limit"),
    )
    parser.add_argument(
        "--site-limit",
        type=int,
        default=5,
        metavar="M",
        help=t("help_search_site_limit"),
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        metavar="SECS",
        help=t("help_search_timeout", secs="5.0"),
    )

    parser.set_defaults(func=handle_search)


def handle_search(args: Namespace) -> None:
    """
    Handler for the `search` subcommand. Loads config, runs the search,
    prompts the user to pick one result, then kicks off download.
    """
    sites: Sequence[str] | None = args.site or None
    keyword: str = args.keyword
    overall_limit = max(1, args.limit)
    per_site_limit = max(1, args.site_limit)
    timeout = max(0.1, float(args.timeout))
    config_path: Path | None = Path(args.config) if args.config else None

    try:
        config_data = load_config(config_path)
    except Exception as e:
        print(t("download_config_load_fail", err=str(e)))
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
            # user cancelled or no valid choice
            return

        adapter = ConfigAdapter(config=config_data, site=chosen["site"])
        books: list[BookConfig] = [{"book_id": chosen["book_id"]}]
        await _download(adapter, chosen["site"], books)

    asyncio.run(_run())


def _prompt_user_select(
    results: Sequence[SearchResult],
) -> SearchResult | None:
    """
    Show a list of search results in a table and prompt the user to pick one.

    :param results: A sequence of SearchResult dicts to display.
    :return: The chosen SearchResult, or None if the user cancels or no selection.
    """
    if not results:
        print(t("no_results"))
        return None

    console = Console()
    table = Table(title="Search Results", show_lines=True, expand=True)
    table.add_column("#", justify="right", no_wrap=True)
    table.add_column("Title", style="bold", overflow="fold")
    table.add_column("Author", overflow="fold")
    table.add_column("Latest", overflow="fold")
    # table.add_column("Words", overflow="fold", justify="right")
    table.add_column("Updated", no_wrap=True)
    table.add_column("Site", no_wrap=True)
    table.add_column("Book ID", overflow="fold")

    for i, r in enumerate(results, 1):
        table.add_row(
            str(i),
            r["title"],
            r["author"],
            r["latest_chapter"],
            # r["word_count"],
            r["update_date"],
            r["site"],
            r["book_id"],
        )
    console.print(table)

    # build the list of valid string choices
    choices = [str(i) for i in range(1, len(results) + 1)]

    choice = Prompt.ask(
        t("prompt_select_index"),
        choices=choices + [""],  # allow blank to cancel
        show_choices=False,
        default="",
        show_default=False,
    ).strip()

    if not choice:
        return None
    return results[int(choice) - 1]


def _prompt_user_select_v1(
    results: Sequence[SearchResult],
    max_attempts: int = 3,
) -> SearchResult | None:
    """
    Display a numbered list of results and prompt the user to pick one.

    :param results: A list of SearchResult dicts.
    :param max_attempts: How many bad inputs to tolerate before giving up.
    :return: The chosen SearchResult, or None if cancelled/failed.
    """
    if not results:
        print(t("no_results"))
        return None

    # Show choices
    for i, r in enumerate(results, start=1):
        print(
            f"[{i}] {r['title']} - {r['author']} | "
            f"Latest: {r['latest_chapter']} | "
            f"Words: {r['word_count']} | "
            f"Updated: {r['update_date']} "
            f"({r['site']}, id={r['book_id']})"
        )

    attempts = 0
    while attempts < max_attempts:
        choice = input(t("prompt_select_index") + ": ").strip()
        if choice == "":
            return None
        if choice.isdigit():
            idx = int(choice)
            if 1 <= idx <= len(results):
                return results[idx - 1]
        print(t("invalid_selection"))
        attempts += 1

    return None
