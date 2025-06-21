#!/usr/bin/env python3
"""
novel_downloader.cli.download
-----------------------------

Download novels from supported sites via CLI.
"""

import asyncio
import getpass
from argparse import Namespace, _SubParsersAction
from collections.abc import Iterable
from dataclasses import asdict
from pathlib import Path
from typing import Any

from novel_downloader.config import ConfigAdapter, load_config
from novel_downloader.core.factory import (
    get_downloader,
    get_exporter,
    get_fetcher,
    get_parser,
)
from novel_downloader.core.interfaces import FetcherProtocol
from novel_downloader.models import BookConfig, LoginField
from novel_downloader.utils.cookies import resolve_cookies
from novel_downloader.utils.i18n import t
from novel_downloader.utils.logger import setup_logging


def register_download_subcommand(subparsers: _SubParsersAction) -> None:  # type: ignore
    parser = subparsers.add_parser("download", help=t("help_download"))

    parser.add_argument("book_ids", nargs="*", help=t("download_book_ids"))
    parser.add_argument(
        "--site", default="qidian", help=t("download_option_site", default="qidian")
    )
    parser.add_argument("--config", type=str, help=t("help_config"))

    parser.add_argument("--start", type=str, help=t("download_option_start"))
    parser.add_argument("--end", type=str, help=t("download_option_end"))

    parser.set_defaults(func=handle_download)


def handle_download(args: Namespace) -> None:
    setup_logging()

    site: str = args.site
    config_path: Path | None = Path(args.config) if args.config else None
    book_ids: list[BookConfig] = _cli_args_to_book_configs(
        args.book_ids,
        args.start,
        args.end,
    )

    print(t("download_site_info", site=site))

    try:
        config_data = load_config(config_path)
    except Exception as e:
        print(t("download_config_load_fail", err=str(e)))
        return

    adapter = ConfigAdapter(config=config_data, site=site)

    if not book_ids:
        try:
            book_ids = adapter.get_book_ids()
        except Exception as e:
            print(t("download_fail_get_ids", err=str(e)))
            return

    valid_books = _filter_valid_book_configs(book_ids)

    if not book_ids:
        print(t("download_no_ids"))
        return

    if not valid_books:
        print(t("download_only_example", example="0000000000"))
        print(t("download_edit_config"))
        return

    asyncio.run(_download(adapter, site, valid_books))


def _cli_args_to_book_configs(
    book_ids: list[str],
    start_id: str | None,
    end_id: str | None,
) -> list[BookConfig]:
    """
    Convert CLI book_ids and optional --start/--end into a list of BookConfig.
    Only the first book_id uses start/end; others are minimal.
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


def _filter_valid_book_configs(
    books: list[BookConfig],
    invalid_ids: Iterable[str] = ("0000000000",),
) -> list[BookConfig]:
    """
    Filter a list of BookConfig:
    - Removes entries with invalid or placeholder book_ids
    - Deduplicates based on book_id while preserving order
    """
    seen = set(invalid_ids)
    result: list[BookConfig] = []

    for book in books:
        book_id = book["book_id"]
        if book_id in seen:
            continue
        seen.add(book_id)
        result.append(book)

    return result


async def _download(
    adapter: ConfigAdapter,
    site: str,
    valid_books: list[BookConfig],
) -> None:
    downloader_cfg = adapter.get_downloader_config()
    fetcher_cfg = adapter.get_fetcher_config()
    parser_cfg = adapter.get_parser_config()
    exporter_cfg = adapter.get_exporter_config()

    parser = get_parser(site, parser_cfg)
    exporter = get_exporter(site, exporter_cfg)
    setup_logging()

    async with get_fetcher(site, fetcher_cfg) as fetcher:
        if downloader_cfg.login_required and not await fetcher.load_state():
            login_data = await _prompt_login_fields(
                fetcher, fetcher.login_fields, downloader_cfg
            )
            if not await fetcher.login(**login_data):
                print(t("download_login_failed"))
                return
            await fetcher.save_state()

        downloader = get_downloader(
            fetcher=fetcher,
            parser=parser,
            site=site,
            config=downloader_cfg,
        )

        for book in valid_books:
            print(t("download_downloading", book_id=book["book_id"], site=site))
            await downloader.download(
                book,
                progress_hook=_print_progress,
            )
            await asyncio.to_thread(exporter.export, book["book_id"])

        if downloader_cfg.login_required and fetcher.is_logged_in:
            await fetcher.save_state()


async def _prompt_login_fields(
    fetcher: FetcherProtocol,
    fields: list[LoginField],
    cfg: Any = None,
) -> dict[str, Any]:
    result: dict[str, Any] = {}
    cfg_dict = asdict(cfg) if cfg else {}

    for field in fields:
        print(f"\n{field.label} ({field.name})")
        if field.description:
            print(f"{t('login_description')}: {field.description}")
        if field.placeholder:
            print(f"{t('login_hint')}: {field.placeholder}")

        if field.type == "manual_login":
            await fetcher.set_interactive_mode(True)
            input(t("login_manual_prompt"))
            await fetcher.set_interactive_mode(False)
            continue

        existing_value = cfg_dict.get(field.name, "").strip()
        if existing_value:
            result[field.name] = existing_value
            print(t("login_use_config"))
            continue

        value: str | dict[str, str]
        while True:
            if field.type == "password":
                value = getpass.getpass(t("login_enter_password"))
            elif field.type == "cookie":
                value = input(t("login_enter_cookie"))
                value = resolve_cookies(value)
            else:
                value = input(t("login_enter_value"))

            if not value and field.default:
                value = field.default

            if not value and field.required:
                print(t("login_required_field"))
            else:
                break

        result[field.name] = value

    return result


async def _print_progress(done: int, total: int) -> None:
    percent = done / total * 100
    print(f"下载进度: {done}/{total} 章 ({percent:.2f}%)")
