#!/usr/bin/env python3
"""
novel_downloader.web.main
-------------------------

Novel Downloader web UI (NiceGUI).

This entry point starts the local server and registers the app's pages.
"""

import argparse

from nicegui import ui

from novel_downloader.web.pages import (
    download_page,  # noqa: F401
    progress_page,  # noqa: F401
    search_page,  # noqa: F401
)


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

    @ui.page("/")  # type: ignore[misc]
    def _index() -> None:
        from novel_downloader.web.pages.search_page import render

        render()

    ui.run(host=host, port=args.port, reload=args.reload)


if __name__ in {"__main__", "__mp_main__"}:
    web_main()
