#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
novel_downloader.cli.main
--------------------------

Unified CLI entry point. Parses arguments and delegates to parser or interactive.

Supports:
- language switching and persistent storage via --lang
- parser mode (default)
- interactive mode via --interactive
"""

import argparse

from novel_downloader.cli.lang import get_text
from novel_downloader.config import save_rules_as_json, set_setting_file
from novel_downloader.utils.logger import setup_logging
from novel_downloader.utils.state import StateManager


def cli_main() -> None:
    setup_logging()
    state_mgr = StateManager()

    lang = state_mgr.get_language()

    parser = argparse.ArgumentParser(description=get_text("cli_desc", lang))

    parser.add_argument(
        "--interactive",
        action="store_true",
        help=get_text("help_interactive", lang),
    )

    parser.add_argument(
        "--lang",
        type=str,
        choices=["zh", "en"],
        default=None,
        help=get_text("help_lang", lang),
    )

    parser.add_argument(
        "--site",
        type=str,
        choices=["qidian", "bqg", "jjwxc"],
        default="qidian",
        help=get_text("help_site", lang),
    )

    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help=get_text("help_config", lang),
    )

    parser.add_argument(
        "--book-id",
        type=str,
        nargs="+",
        help=get_text("help_book_id", lang),
    )

    parser.add_argument("--set-setting", type=str, help="Set custom YAML setting file")

    parser.add_argument(
        "--update-rules",
        type=str,
        help="Path to a TOML/YAML/JSON file containing updated site rules.",
    )

    args = parser.parse_args()

    if args.set_setting:
        set_setting_file(args.set_setting)
        print(f"[Main] Custom setting from {args.set_setting}")
        return

    if args.update_rules:
        try:
            save_rules_as_json(args.update_rules)
            print(f"[MAIN] Successfully updated rules from {args.update_rules}")
        except Exception as e:
            print(f"[MAIN] Failed to update rules: {e}")
        return

    if args.lang:
        state_mgr.set_language(args.lang)
        print(f"[MAIN] {get_text('msg_lang_saved', args.lang)}: {args.lang}")
        return

    if args.interactive:
        from .interactive import interactive_main

        interactive_main(lang=lang)
    else:
        from .parser import run_parser_mode

        run_parser_mode(args, lang=lang)


if __name__ == "__main__":
    cli_main()
