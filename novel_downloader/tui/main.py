#!/usr/bin/env python3
"""
novel_downloader.tui.main
-------------------------

"""

from novel_downloader.tui.app import NovelDownloaderTUI


def tui_main() -> None:
    app = NovelDownloaderTUI()
    app.run()


if __name__ == "__main__":
    tui_main()
