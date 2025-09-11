#!/usr/bin/env python3
"""
novel_downloader.web.pages.history
----------------------------------

"""

from __future__ import annotations

import time
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from nicegui import ui
from nicegui.events import ValueChangeEventArguments

from novel_downloader.config import get_config_value
from novel_downloader.web.components import navbar
from novel_downloader.web.services import setup_dialog

_OUTPUT_DIR = Path(get_config_value(["general", "output_dir"], "./downloads"))
_PAGE_SIZE = 20
_PAGER_WIDTH = 9

SortKey = Literal["name", "mtime"]
TypeFilter = Literal["All", "txt", "epub"]


@dataclass(frozen=True)
class FileItem:
    path: Path
    name: str
    ext: str  # '.txt' or '.epub'
    mtime: float


def _scan_files(output_dir: Path) -> list[FileItem]:
    """Return all *.txt and *.epub files in output_dir as FileItem list."""
    items: list[FileItem] = []
    for ext in (".txt", ".epub"):
        for p in output_dir.glob(f"*{ext}"):
            if p.is_file():
                items.append(
                    FileItem(
                        path=p,
                        name=p.name,
                        ext=p.suffix.lower(),
                        mtime=p.stat().st_mtime,
                    )
                )
    return items


def _apply_filter(items: Iterable[FileItem], type_filter: TypeFilter) -> list[FileItem]:
    """Filter by extension; 'All' returns everything."""
    if type_filter == "All":
        return list(items)
    return [it for it in items if it.ext == f".{type_filter}"]


def _apply_sort(items: list[FileItem], sort_by: SortKey) -> list[FileItem]:
    """Sort items by name (asc) or modified time (desc newest first)."""
    if sort_by == "name":
        return sorted(items, key=lambda it: it.name.lower())
    return sorted(items, key=lambda it: it.mtime, reverse=True)


def _render_file_card(item: FileItem) -> None:
    """Render a single file as a card with icon, meta, and a Download button."""
    url = f"/downloads/{item.name}?v={int(item.mtime)}"
    human_mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item.mtime))

    with ui.card().classes("w-full"), ui.row().classes("items-start gap-4"):
        if item.ext == ".epub":
            ui.icon("menu_book").classes("text-4xl")
        else:  # .txt
            ui.icon("description").classes("text-4xl")

        # Meta & actions
        with ui.column().classes("min-w-0"):
            ui.label(item.name).classes("text-base font-medium break-words")
            ui.label(f"Modified: {human_mtime}").classes("text-xs text-gray-500")
            with ui.row().classes("mt-2"):
                ui.button(
                    "Download",
                    icon="download",
                    on_click=lambda e, url=url: ui.download(url),
                ).props("outline size=sm")


@ui.page("/history")  # type: ignore[misc]
def page_history() -> None:
    navbar("history")
    ui.label("下载历史").classes("text-xl font-bold my-4")
    setup_dialog()

    # Reactive state
    page: int = 1
    type_filter: TypeFilter = "All"
    sort_by: SortKey = "name"

    # Controls
    with ui.row().classes("items-center gap-3 my-2 flex-wrap"):
        ui.label("Type:")
        ui.select(
            ["All", "txt", "epub"],
            value="All",
            with_input=False,
            on_change=lambda e: _on_type_change(e),
        ).props("dense outlined")

        ui.label("Sort by:")
        ui.select(
            {"name": "name", "mtime": "modified time"},
            value="name",
            with_input=False,
            on_change=lambda e: _on_sort_change(e),
        ).props("dense outlined")

    list_area = ui.column().classes("w-full gap-3")
    pager_area = ui.row().classes("justify-center my-4 w-full")

    def _load_all() -> list[FileItem]:
        return _scan_files(_OUTPUT_DIR)

    def _refresh() -> None:
        nonlocal page

        all_items = _load_all()
        filtered = _apply_filter(all_items, type_filter)
        sorted_items = _apply_sort(filtered, sort_by)

        total = len(sorted_items)
        total_pages = max(1, (total + _PAGE_SIZE - 1) // _PAGE_SIZE)

        # clamp page after filter/sort changes
        page = min(max(page, 1), total_pages)

        start = (page - 1) * _PAGE_SIZE
        end = min(start + _PAGE_SIZE, total)
        current_slice = sorted_items[start:end]

        list_area.clear()
        with list_area:
            if not current_slice:
                ui.label("No files found.").classes("text-gray-500")
            else:
                for item in current_slice:
                    _render_file_card(item)

        pager_area.clear()
        if total_pages > 1:

            def _on_page_change(e: ValueChangeEventArguments) -> None:
                nonlocal page
                page = int(e.value)
                _refresh()

            with pager_area:
                ui.pagination(
                    1,  # min
                    total_pages,  # max
                    direction_links=True,
                    value=page,
                    on_change=_on_page_change,
                ).props(f"max-pages={_PAGER_WIDTH} boundary-numbers ellipses")

    # Handlers
    def _on_type_change(e: ValueChangeEventArguments) -> None:
        nonlocal type_filter, page
        type_filter = e.value  # "All" | "txt" | "epub"
        page = 1
        _refresh()

    def _on_sort_change(e: ValueChangeEventArguments) -> None:
        nonlocal sort_by, page
        sort_by = e.value  # "name" | "mtime"
        page = 1
        _refresh()

    # Initial render
    _refresh()
