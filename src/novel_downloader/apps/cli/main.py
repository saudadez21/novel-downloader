#!/usr/bin/env python3
"""
novel_downloader.apps.cli.main
------------------------------

Unified CLI entry point. Parses arguments and delegates to parser or interactive.
"""

import argparse

from novel_downloader.apps.cli.commands import commands
from novel_downloader.infra.i18n import t


def cli_main() -> None:
    parser = argparse.ArgumentParser(description=t("Novel Downloader CLI tool."))
    subparsers = parser.add_subparsers(dest="command", required=True)

    for cmd in commands:
        cmd.register(subparsers)

    args = parser.parse_args()
    if hasattr(args, "func"):
        try:
            args.func(args)
        except KeyboardInterrupt as err:
            print("\nAborted.")
            raise SystemExit(1) from err
    else:
        parser.print_help()


if __name__ == "__main__":
    cli_main()
