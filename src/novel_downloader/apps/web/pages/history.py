#!/usr/bin/env python3
"""
novel_downloader.apps.web.pages.history
---------------------------------------

"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import quote

from nicegui import ui
from nicegui.events import KeyEventArguments, ValueChangeEventArguments

from novel_downloader.infra.config import get_config_value
from novel_downloader.infra.i18n import t

from ..components import navbar
from ..services import setup_dialog

_EXTS = {"txt", "epub"}
_OUTPUT_DIR = Path(get_config_value(["general", "output_dir"], "./downloads"))
_PAGE_SIZE = 20
_PAGER_WIDTH = 9

SortKey = Literal["name", "mtime"]
SortOrder = Literal["asc", "desc"]
TypeFilter = Literal["All", "txt", "epub"]


@dataclass(frozen=True)
class FileItem:
    path: Path
    name: str
    ext: str  # 'txt' or 'epub'
    mtime: float


def _scan_files() -> list[FileItem]:
    """Scan the output directory for txt/epub files."""
    try:
        it = os.scandir(_OUTPUT_DIR)
    except FileNotFoundError:
        return []
    items: list[FileItem] = []
    for entry in it:
        try:
            if not entry.is_file():
                continue
            ext = Path(entry.name).suffix.lower().lstrip(".")
            if ext not in _EXTS:
                continue
            st = entry.stat()
            items.append(
                FileItem(
                    path=Path(entry.path),
                    name=entry.name,
                    ext=ext,
                    mtime=st.st_mtime,
                )
            )
        except FileNotFoundError:
            continue
    return items


def _apply_filter(items: list[FileItem], type_filter: TypeFilter) -> list[FileItem]:
    """Filter by extension; 'All' returns everything."""
    if type_filter == "All":
        return items
    return [it for it in items if it.ext == type_filter]


def _apply_sort(
    items: list[FileItem], sort_by: SortKey, order: SortOrder
) -> list[FileItem]:
    """Sort items by name/mtime in given order."""
    reverse = order == "desc"
    if sort_by == "name":
        return sorted(items, key=lambda it: it.name.lower(), reverse=reverse)
    return sorted(items, key=lambda it: it.mtime, reverse=reverse)


def _render_file_card(item: FileItem) -> None:
    """Render a single file as a card with icon, meta, and a Download button."""
    url = f"/downloads/{quote(item.name)}?v={int(item.mtime)}"
    human_mtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(item.mtime))

    with ui.card().classes("w-full"), ui.row().classes("items-start gap-4"):
        if item.ext == "epub":
            ui.icon("menu_book").classes("text-4xl")
        else:  # txt
            ui.icon("description").classes("text-4xl")

        # Meta & actions
        with ui.column().classes("min-w-0"):
            ui.label(item.name).classes("text-base font-medium break-words")
            ui.label(f"Modified: {human_mtime}").classes("text-xs text-caption")
            with ui.row().classes("mt-2"):
                ui.button(
                    "Download",
                    icon="download",
                    on_click=lambda e, url=url: ui.download(url),
                ).props("outline size=sm")


@ui.page("/history")  # type: ignore[misc]
def page_history() -> None:
    navbar("history")
    setup_dialog()

    # reactive state
    page: int = 1
    type_filter: TypeFilter = "All"
    sort_by: SortKey = "mtime"
    sort_order: SortOrder = "desc"

    # cached lists
    all_items: list[FileItem] = []
    sorted_items: list[FileItem] = []

    # centered, responsive container
    with ui.column().classes("w-full max-w-screen-lg min-w-[320px] mx-auto gap-4"):
        ui.label(t("Download History")).classes("text-lg")

        # Toolbar (filters & sorting)
        with ui.card().classes("w-full"), ui.row().classes(
            "items-center gap-3 w-full flex-wrap"
        ):
            ui.label(t("Type")).classes("text-sm text-caption")
            type_sel = (
                ui.select(
                    ["All", "txt", "epub"],
                    value=type_filter,
                    with_input=False,
                )
                .props("dense outlined")
                .classes("w-[140px]")
            )

            ui.separator().props("vertical").classes(
                "mx-1 self-stretch hidden md:block"
            )

            ui.label(t("Sort Field")).classes("text-sm text-caption")
            sort_key_sel = (
                ui.select(
                    {"name": t("Filename"), "mtime": t("Modified Time")},
                    value=sort_by,
                    with_input=False,
                )
                .props("dense outlined")
                .classes("w-[160px]")
            )

            sort_order_sel = ui.toggle(
                {"asc": t("Ascending"), "desc": t("Descending")}, value=sort_order
            ).props("dense")

            def _on_refresh() -> None:
                _reload()
                _refresh()

            ui.button(
                t("Refresh"),
                icon="refresh",
                on_click=_on_refresh,
            ).props("dense flat")

        # status line (counts)
        status_area = ui.row().classes(
            "items-center gap-2 w-full text-sm text-secondary"
        )

        # list + pager
        list_area = ui.column().classes("w-full gap-3")
        pager_area = ui.row().classes("justify-center my-2 w-full")

        def _reload() -> None:
            """Scan filesystem and refresh full list."""
            nonlocal all_items
            all_items = _scan_files()
            _recompute_from_cache()

        def _recompute_from_cache() -> None:
            """Recompute filtered+sorted items from cached all_items."""
            nonlocal sorted_items, page
            filtered = _apply_filter(all_items, type_filter)
            sorted_items = _apply_sort(filtered, sort_by, sort_order)
            page = 1

        def _refresh_status(total: int, filtered_total: int) -> None:
            status_area.clear()
            with status_area:
                if filtered_total == total:
                    ui.label(t("Total {total} files").format(total=total))
                else:
                    ui.label(
                        t("Total {total} files · After filter {filtered} files").format(
                            total=total, filtered=filtered_total
                        )
                    )

        def _refresh() -> None:
            nonlocal page
            total_all = len(all_items)
            total = len(sorted_items)
            total_pages = max(1, (total + _PAGE_SIZE - 1) // _PAGE_SIZE)

            # clamp page
            page = min(max(page, 1), total_pages)

            start = (page - 1) * _PAGE_SIZE
            end = min(start + _PAGE_SIZE, total)
            current_slice = sorted_items[start:end]

            _refresh_status(total_all, total)

            list_area.clear()
            with list_area:
                if not current_slice:
                    ui.label(t("No files")).classes("text-caption")
                else:
                    for item in current_slice:
                        _render_file_card(item)

            pager_area.clear()
            if total_pages > 1:

                def _on_page_change(e: ValueChangeEventArguments) -> None:
                    nonlocal page
                    try:
                        page = int(e.value)
                    except Exception:
                        page = 1
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
            nonlocal type_filter
            type_filter = e.value
            _recompute_from_cache()
            _refresh()

        def _on_sort_key_change(e: ValueChangeEventArguments) -> None:
            nonlocal sort_by
            sort_by = e.value
            _recompute_from_cache()
            _refresh()

        def _on_sort_order_change(e: ValueChangeEventArguments) -> None:
            nonlocal sort_order, sorted_items, page
            new_order = e.value
            # Optimization: if only order changes, reverse current list
            if sort_order != new_order and len(sorted_items) > 1:
                sorted_items.reverse()
                sort_order = new_order
                page = 1
                _refresh()
            else:
                sort_order = new_order
                _recompute_from_cache()
                _refresh()

        type_sel.on_value_change(_on_type_change)
        sort_key_sel.on_value_change(_on_sort_key_change)
        sort_order_sel.on_value_change(_on_sort_order_change)

        # Keyboard: left/right to change page (keyup only)
        def _on_key(e: KeyEventArguments) -> None:
            if not e.action.keyup:
                return
            nonlocal page
            total = len(sorted_items)
            total_pages = max(1, (total + _PAGE_SIZE - 1) // _PAGE_SIZE)

            if e.key == "ArrowLeft" and page > 1:
                page -= 1
                _refresh()
            elif e.key == "ArrowRight" and page < total_pages:
                page += 1
                _refresh()

        ui.keyboard(on_key=_on_key)

        # Initial render
        _reload()
        _refresh()
