#!/usr/bin/env python3
"""
novel_downloader.cli.download
-----------------------------

Download novels from supported sites via the CLI.
"""

from __future__ import annotations

import asyncio
from argparse import Namespace, _SubParsersAction
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from novel_downloader.cli import ui
from novel_downloader.config import ConfigAdapter, load_config
from novel_downloader.core import get_downloader, get_exporter, get_fetcher, get_parser
from novel_downloader.models import BookConfig, LoginField
from novel_downloader.utils.cookies import parse_cookies
from novel_downloader.utils.i18n import t
from novel_downloader.utils.logger import setup_logging


def register_download_subcommand(subparsers: _SubParsersAction) -> None:  # type: ignore
    """Register the `download` subcommand and its options."""
    parser = subparsers.add_parser("download", help=t("help_download"))

    parser.add_argument("book_ids", nargs="*", help=t("download_book_ids"))
    parser.add_argument(
        "--site", default="qidian", help=t("download_option_site", default="qidian")
    )
    parser.add_argument("--config", type=str, help=t("help_config"))

    parser.add_argument("--start", type=str, help=t("download_option_start"))
    parser.add_argument("--end", type=str, help=t("download_option_end"))

    parser.add_argument(
        "--no-export",
        action="store_true",
        help=t("download_option_no_export"),
    )

    parser.set_defaults(func=handle_download)


def handle_download(args: Namespace) -> None:
    """Handle the `download` subcommand."""
    site: str = args.site
    config_path: Path | None = Path(args.config) if args.config else None
    book_ids: list[BookConfig] = _cli_args_to_book_configs(
        args.book_ids, args.start, args.end
    )
    no_export: bool = getattr(args, "no_export", False)

    ui.info(t("download_site_info", site=site))

    try:
        config_data = load_config(config_path)
    except Exception as e:
        ui.error(t("download_config_load_fail", err=str(e)))
        return

    adapter = ConfigAdapter(config=config_data, site=site)

    if not book_ids:
        try:
            book_ids = adapter.get_book_ids()
        except Exception as e:
            ui.error(t("download_fail_get_ids", err=str(e)))
            return

    valid_books = _filter_valid_book_configs(book_ids)

    if not book_ids:
        ui.warn(t("download_no_ids"))
        return

    if not valid_books:
        ui.warn(t("download_only_example", example="0000000000"))
        ui.info(t("download_edit_config"))
        return

    asyncio.run(_download(adapter, site, valid_books, no_export=no_export))


def _cli_args_to_book_configs(
    book_ids: list[str],
    start_id: str | None,
    end_id: str | None,
) -> list[BookConfig]:
    """
    Convert CLI arguments into a list of `BookConfig`.
    Only the first book_id takes `start_id`/`end_id`.
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
    Filter out placeholder or duplicate book IDs, preserving order.

    :param books: The list to filter.
    :param invalid_ids: A set/iterable of IDs to treat as invalid.
    :return: De-duplicated, valid list.
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
    *,
    no_export: bool = False,
) -> None:
    """
    Perform the download flow:
      * Init components
      * Login if required
      * Download each requested book
      * Export with configured exporter
    """
    downloader_cfg = adapter.get_downloader_config()
    fetcher_cfg = adapter.get_fetcher_config()
    parser_cfg = adapter.get_parser_config()
    exporter_cfg = adapter.get_exporter_config()
    login_cfg = adapter.get_login_config()
    log_level = adapter.get_log_level()
    setup_logging(log_level=log_level)

    parser = get_parser(site, parser_cfg)
    exporter = None
    if not no_export:
        exporter = get_exporter(site, exporter_cfg)
    else:
        ui.info(t("download_export_skipped"))

    async with get_fetcher(site, fetcher_cfg) as fetcher:
        if downloader_cfg.login_required and not await fetcher.load_state():
            login_data = await _prompt_login_fields(fetcher.login_fields, login_cfg)
            if not await fetcher.login(**login_data):
                ui.error(t("download_login_failed"))
                return
            await fetcher.save_state()

        downloader = get_downloader(
            fetcher=fetcher, parser=parser, site=site, config=downloader_cfg
        )

        for book in valid_books:
            ui.info(t("download_downloading", book_id=book["book_id"], site=site))
            await downloader.download(book, progress_hook=_print_progress)

            if not no_export and exporter is not None:
                await asyncio.to_thread(exporter.export, book["book_id"])

        if downloader_cfg.login_required and fetcher.is_logged_in:
            await fetcher.save_state()


async def _prompt_login_fields(
    fields: list[LoginField],
    login_config: dict[str, str] | None = None,
) -> dict[str, Any]:
    """
    Prompt for required login fields, honoring defaults and config-provided values.

    :param fields: Field descriptors from the fetcher (name/label/type/etc.).
    :param login_config: Optional values already configured by the user.
    :return: A dict suitable to pass to `fetcher.login(**kwargs)`.
    """
    login_config = login_config or {}
    result: dict[str, Any] = {}

    for field in fields:
        ui.info(f"\n{field.label} ({field.name})")
        if field.description:
            ui.info(f"{t('login_description')}: {field.description}")
        if field.placeholder:
            ui.info(f"{t('login_hint')}: {field.placeholder}")

        existing_value = login_config.get(field.name, "").strip()
        if existing_value:
            result[field.name] = existing_value
            ui.info(t("login_use_config"))
            continue

        value: str | dict[str, str]
        while True:
            if field.type == "password":
                value = ui.prompt_password(t("login_enter_password"))
            elif field.type == "cookie":
                value = ui.prompt(t("login_enter_cookie"))
                value = parse_cookies(value)
            else:
                value = ui.prompt(t("login_enter_value"))

            if not value and field.default:
                value = field.default

            if not value and field.required:
                ui.warn(t("login_required_field"))
            else:
                break

        result[field.name] = value

    return result


async def _print_progress(done: int, total: int) -> None:
    """Progress hook passed into the downloader."""
    ui.print_progress(
        done, total, prefix=t("download_progress_prefix"), unit="chapters"
    )
