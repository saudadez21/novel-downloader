#!/usr/bin/env python3
"""
novel_downloader.apps.web.components.navigation
-----------------------------------------------

A tiny NiceGUI component that renders the app's top navigation bar
"""

from nicegui import ui

from novel_downloader.utils.i18n import t


def navbar(active: str) -> None:
    """
    Render the site-wide navigation header.

    :param active: Key of the current page to highlight.
    """
    with (
        ui.header().classes("px-3 items-center justify-between bg-primary text-white"),
        ui.row().classes("items-center gap-2 flex-wrap"),
    ):
        _nav_btn(t("Search"), "/", active == "search", icon="search")
        _nav_btn(t("Download"), "/download", active == "download", icon="download")
        _nav_btn(
            t("In Progress"), "/progress", active == "progress", icon="cloud_download"
        )
        _nav_btn(t("History"), "/history", active == "history", icon="history")


def _nav_btn(label: str, path: str, is_active: bool, icon: str | None = None) -> None:
    if is_active:
        ui.button(label, icon=icon, on_click=lambda: ui.navigate.to(path)).props(
            "unelevated color=white text-color=primary"
        )
    else:
        ui.button(label, icon=icon, on_click=lambda: ui.navigate.to(path)).props(
            "flat text-color=white"
        )
