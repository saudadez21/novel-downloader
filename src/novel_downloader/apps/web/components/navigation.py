#!/usr/bin/env python3
"""
novel_downloader.apps.web.components.navigation
-----------------------------------------------

A tiny NiceGUI component that renders the app's top navigation bar
"""

from nicegui import ui
from nicegui.events import ClickEventArguments

from novel_downloader.infra.i18n import t

_dark_state = {"value": False}


def _theme_props(is_dark: bool | None) -> str:
    icon = "dark_mode" if is_dark else "light_mode"
    return f"flat round dense icon={icon} text-color=white"


def navbar(active: str) -> None:
    """
    Render the site-wide navigation header.

    :param active: Key of the current page to highlight.
    """
    dark = ui.dark_mode(value=_dark_state["value"])

    def toggle(e: ClickEventArguments) -> None:
        new_val = not dark.value
        dark.set_value(new_val)
        _dark_state["value"] = new_val
        theme_btn.props(_theme_props(new_val))

    with ui.header().classes("px-3 items-center justify-between bg-primary text-white"):
        with ui.row().classes("items-center gap-2 flex-wrap"):
            _nav_btn(t("Search"), "/", active == "search", icon="search")
            _nav_btn(t("Download"), "/download", active == "download", icon="download")
            _nav_btn(
                t("In Progress"),
                "/progress",
                active == "progress",
                icon="cloud_download",
            )
            _nav_btn(t("History"), "/history", active == "history", icon="history")

        with ui.row().classes("items-center gap-2"):
            theme_btn = ui.button(on_click=toggle).props(_theme_props(dark.value))


def _nav_btn(label: str, path: str, is_active: bool, icon: str | None = None) -> None:
    if is_active:
        ui.button(label, icon=icon, on_click=lambda: ui.navigate.to(path)).props(
            "unelevated color=white text-color=primary"
        )
    else:
        ui.button(label, icon=icon, on_click=lambda: ui.navigate.to(path)).props(
            "flat text-color=white"
        )
