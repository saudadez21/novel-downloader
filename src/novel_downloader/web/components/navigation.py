#!/usr/bin/env python3
"""
novel_downloader.web.components.navigation
------------------------------------------

A tiny NiceGUI component that renders the app's top navigation bar
"""

from nicegui import ui


def navbar(active: str) -> None:
    """
    Render the site-wide navigation header.

    :param active: Key of the current page to highlight.
    """
    with (
        ui.header().classes("px-3 items-center justify-between bg-primary text-white"),
        ui.row().classes("items-center gap-2 flex-wrap"),
    ):
        _nav_btn("搜索", "/", active == "search", icon="search")
        _nav_btn("下载", "/download", active == "download", icon="download")
        _nav_btn("正在下载", "/progress", active == "progress", icon="cloud_download")


def _nav_btn(label: str, path: str, is_active: bool, icon: str | None = None) -> None:
    if is_active:
        ui.button(label, icon=icon, on_click=lambda: ui.navigate.to(path)).props(
            "unelevated color=white text-color=primary"
        )
    else:
        ui.button(label, icon=icon, on_click=lambda: ui.navigate.to(path)).props(
            "flat text-color=white"
        )
