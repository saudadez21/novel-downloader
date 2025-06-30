#!/usr/bin/env python3
"""
novel_downloader.cli.main
-------------------------

Unified CLI entry point. Parses arguments and delegates to parser or interactive.
"""

import argparse

from novel_downloader.utils.i18n import t

from .clean import register_clean_subcommand
from .config import register_config_subcommand
from .download import register_download_subcommand
from .export import register_export_subcommand


def cli_main() -> None:
    parser = argparse.ArgumentParser(description=t("cli_help"))
    subparsers = parser.add_subparsers(dest="command", required=True)

    register_clean_subcommand(subparsers)
    register_config_subcommand(subparsers)
    register_download_subcommand(subparsers)
    register_export_subcommand(subparsers)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    cli_main()
