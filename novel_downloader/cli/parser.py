#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.cli.parser
----------------------------

Command-line parser mode for novel_downloader.
This is the traditional CLI entry point with --config, --book-id, etc.
"""

from argparse import Namespace
from dataclasses import asdict, is_dataclass
from pprint import pprint
from typing import Any

from novel_downloader.cli.lang import get_text
from novel_downloader.config import ConfigAdapter, load_config
from novel_downloader.core import get_requester


def print_config(title: str, config_obj: Any) -> None:
    """
    Print the content of a dataclass-style config object.
    """
    print(f"\n{title}")
    if is_dataclass(config_obj) and not isinstance(config_obj, type):
        pprint(asdict(config_obj), sort_dicts=False)
    else:
        pprint(vars(config_obj), sort_dicts=False)
    return


def run_parser_mode(args: Namespace, lang: str = "zh") -> None:
    print("CLI support is not implemented yet.")
    print(get_text("label_config", lang), ":", args.config)
    print(get_text("label_book_ids", lang), ":", args.book_id)
    print(get_text("label_site", lang), ":", args.site)

    config_data = load_config(args.config)
    adapter = ConfigAdapter(config=config_data, site=args.site)

    requester_cfg = adapter.get_requester_config()
    downloader_cfg = adapter.get_downloader_config()
    parser_cfg = adapter.get_parser_config()
    saver_cfg = adapter.get_saver_config()

    print_config("RequesterConfig", requester_cfg)
    print_config("DownloaderConfig", downloader_cfg)
    print_config("ParserConfig", parser_cfg)
    print_config("SaverConfig", saver_cfg)

    if args.book_id:
        book_ids = args.book_id
    else:
        try:
            book_ids = adapter.get_book_ids()
        except Exception as e:
            print("Failed to get book_ids from config:", e)
            return

    invalid_ids = {"0000000000"}
    valid_book_ids = [bid for bid in book_ids if bid not in invalid_ids]

    if not book_ids:
        print("No book_ids found in config.")
        return

    if not valid_book_ids:
        print("Only example book_ids found (e.g. '0000000000').")
        print("Please edit your config and replace them with real book IDs.")
        return

    print(f"Starting download for {len(valid_book_ids)} book(s): {valid_book_ids}")

    curr_requester = get_requester(args.site, requester_cfg)

    success = curr_requester.login()
    _ = success
    input("Parse...")
    curr_requester.shutdown()

    return
