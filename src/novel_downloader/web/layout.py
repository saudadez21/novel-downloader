#!/usr/bin/env python3
"""
novel_downloader.web.layout
---------------------------

"""

from nicegui import ui


def navbar(active: str) -> None:
    with (
        ui.header().classes("px-3 items-center justify-between"),
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
