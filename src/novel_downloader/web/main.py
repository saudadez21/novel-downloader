#!/usr/bin/env python3
"""
novel_downloader.web.main
-------------------------

Novel Downloader web UI (NiceGUI).

This entry point starts the local server and registers the app's pages.
"""

import argparse
from pathlib import Path

from nicegui import app, ui

import novel_downloader.web.pages  # noqa: F401
from novel_downloader.config import get_config_value
from novel_downloader.utils.logger import setup_logging


def mount_exports() -> None:
    output_dir = get_config_value(["general", "output_dir"], "./downloads")
    out = Path(output_dir).expanduser().resolve()
    out.mkdir(parents=True, exist_ok=True)
    # serves /download/<filename> from the export dir
    app.add_static_files("/download", local_directory=out)


def web_main() -> None:
    p = argparse.ArgumentParser(
        description="Novel Downloader web UI.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument(
        "--listen",
        choices=["local", "public"],
        default="local",
        help=(
            "Bind address mode: 'local' binds to 127.0.0.1; "
            "'public' binds to 0.0.0.0."
        ),
    )
    p.add_argument(
        "--port",
        type=int,
        default=8080,
        help="TCP port to serve the app on.",
    )
    p.add_argument(
        "--reload",
        action="store_true",
        help="Enable autoreload on code changes (development).",
    )
    args = p.parse_args()

    host = "127.0.0.1" if args.listen == "local" else "0.0.0.0"

    log_level = get_config_value(["general", "debug", "log_level"], "INFO")
    setup_logging(log_level=log_level)

    app.on_startup(mount_exports)
    ui.run(host=host, port=args.port, reload=args.reload)


if __name__ in {"__main__", "__mp_main__"}:
    web_main()
