#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.cli.parser
----------------------------

Command-line parser mode for novel_downloader.
This is the traditional CLI entry point with --config, --book-id, etc.
"""

from argparse import Namespace

from novel_downloader.cli.lang import get_text
from novel_downloader.config import ConfigAdapter, load_config
from novel_downloader.core import (
    get_downloader,
    get_parser,
    get_requester,
    get_saver,
)


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
    curr_parser = get_parser(args.site, parser_cfg)
    curr_saver = get_saver(args.site, saver_cfg)
    curr_downloader = get_downloader(
        requester=curr_requester,
        parser=curr_parser,
        saver=curr_saver,
        site=args.site,
        config=downloader_cfg,
    )

    curr_downloader.download(valid_book_ids)

    input("Parse...")
    curr_requester.shutdown()

    return
