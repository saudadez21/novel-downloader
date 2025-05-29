#!/usr/bin/env python3
"""
novel_downloader.tui.app
------------------------

"""


from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Footer, Header

from novel_downloader.tui.screens.home import HomeScreen


class NovelDownloaderTUI(App):  # type: ignore[misc]
    TITLE = "Novel Downloader TUI"
    SCREENS = {
        "home": HomeScreen,
    }

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(id="main_area")
        yield Footer()

    def on_mount(self) -> None:
        self.push_screen("home")
