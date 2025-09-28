#!/usr/bin/env python3
"""
novel_downloader.apps.web.pages.search
--------------------------------------

Search UI with a settings dropdown, persistent state, and paginated results.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable
from contextlib import aclosing, suppress
from typing import Any

from nicegui import ui
from nicegui.elements.number import Number
from nicegui.events import KeyEventArguments, ValueChangeEventArguments

from novel_downloader.apps.constants import SEARCH_SUPPORT_SITES
from novel_downloader.infra.i18n import t
from novel_downloader.plugins.searching import search_stream
from novel_downloader.schemas import SearchResult

from ..components import navbar
from ..services import manager, setup_dialog

_DEFAULT_TIMEOUT = 10.0
_DEFAULT_SITE_LIMIT = 30
_PAGE_SIZE = 20
_PAGER_WIDTH = 9

_STATE: dict[str, dict[str, Any]] = {}


def _get_state() -> dict[str, Any]:
    cid = ui.context.client.id
    if cid not in _STATE:
        _STATE[cid] = {
            "query": "",
            "sites": None,  # list[str] | None (None => search all)
            "per_site_limit": _DEFAULT_SITE_LIMIT,
            "timeout": _DEFAULT_TIMEOUT,
            "results": [],  # list[SearchResult]
            "page": 1,
            "page_size": _PAGE_SIZE,
            "search_task": None,  # asyncio.Task | None
            "searching": False,  # bool
            "sort_key": "priority",  # site | title | author | priority
            "sort_order": "asc",  # asc | desc
        }
    return _STATE[cid]


def _cleanup_state() -> None:
    cid = ui.context.client.id
    # cancel any in-flight search task to avoid leaks
    st = _STATE.get(cid)
    if st and isinstance(st.get("search_task"), asyncio.Task):
        task: asyncio.Task[Any] = st["search_task"]
        if not task.done():
            task.cancel()
    _STATE.pop(cid, None)


def _coerce_timeout(inp: Number) -> float:
    v = inp.value
    try:
        v = float(v)
        if v <= 0:
            raise ValueError
    except (TypeError, ValueError):
        ui.notify(t("Timeout must be > 0 seconds, reset to 10.0"), type="warning")
        v = _DEFAULT_TIMEOUT
    inp.set_value(v)
    inp.sanitize()
    return float(v)


def _coerce_psl(inp: Number) -> int:
    v = inp.value
    try:
        v = int(v)
        if v <= 0:
            raise ValueError
    except (TypeError, ValueError):
        ui.notify(
            t("Per-site limit must be a positive integer, reset to 30"), type="warning"
        )
        v = _DEFAULT_SITE_LIMIT
    inp.set_value(v)
    inp.sanitize()
    return int(v)


def _render_placeholder_cover() -> None:
    with ui.element("div").classes(
        "w-[72px] h-[96px] bg-grey-3 rounded-md flex items-center justify-center"
    ):
        ui.icon("book").classes("text-secondary text-3xl")


def _site_label(site_key: str) -> str:
    return SEARCH_SUPPORT_SITES.get(site_key, site_key)


def _norm_text(v: Any) -> str:
    return str(v or "").strip().casefold()


def _apply_sort(state: dict[str, Any]) -> None:
    """Sort state['results'] in place according to sort_key/order."""
    key = state.get("sort_key") or "priority"
    order = state.get("sort_order") or "desc"
    reverse = order == "desc"

    def k_site(r: SearchResult) -> tuple[str, str, str]:
        # Sort by Chinese label; tie-break by site key for stability, then title
        return (
            _norm_text(_site_label(r.get("site", "unknown"))),
            _norm_text(r.get("site")),
            _norm_text(r.get("title")),
        )

    def k_title(r: SearchResult) -> tuple[str, str]:
        return (_norm_text(r.get("title")), _norm_text(r.get("author")))

    def k_author(r: SearchResult) -> tuple[str, str]:
        return (_norm_text(r.get("author")), _norm_text(r.get("title")))

    def k_priority(r: SearchResult) -> float:
        try:
            return float(r.get("priority", 0))
        except Exception:
            return 0.0

    key_map: dict[str, Callable[[SearchResult], Any]] = {
        "site": k_site,
        "title": k_title,
        "author": k_author,
        "priority": k_priority,
    }
    key_fn = key_map.get(key, k_priority)

    # NOTE: for numeric priority, reverse flag already handles desc/asc
    state["results"].sort(key=key_fn, reverse=reverse)


def _render_result_row(r: SearchResult) -> None:
    with (
        ui.card().classes("w-full"),
        ui.row().classes("items-start justify-between w-full gap-3"),
    ):
        cover = (r.get("cover_url") or "").strip()
        if cover.startswith(("http://", "https://")):
            ui.image(cover).classes("w-[72px] h-[96px] object-cover rounded-md")
        else:
            _render_placeholder_cover()

        with ui.column().classes("gap-1 grow"):
            ui.link(r["title"], r["book_url"], new_tab=True).classes(
                "text-base font-medium"
            )
            ui.label(
                t("{author} · {words} · Updated at {date}").format(
                    author=r["author"], words=r["word_count"], date=r["update_date"]
                )
            ).classes("text-xs text-caption")
            ui.label(r["latest_chapter"]).classes("text-sm text-secondary")

            ui.label(f"{_site_label(r['site'])} · ID: {r['book_id']}").classes(
                "text-xs text-caption"
            )

        async def _add_task() -> None:
            title = r["title"]
            ui.notify(t("Task added: {title}").format(title=title))
            await manager.add_task(title=title, site=r["site"], book_id=r["book_id"])

        ui.button(t("Download"), color="primary", on_click=_add_task).props(
            "unelevated"
        )


def _build_settings_dropdown(
    state: dict[str, Any],
) -> tuple[Callable[[], list[str] | None], Callable[[], int], Callable[[], float]]:
    """
    Create settings button + anchored menu with initial values from state.

    Returns a tuple of getter functions:
      * get_sites(): list of site keys, or None if none selected
      * get_psl(): per-site limit (int)
      * get_timeout(): timeout (float)
    """
    site_cbs: dict[str, Any] = {}

    settings_btn = ui.button(t("Settings")).props("outline icon=settings")
    with settings_btn:
        menu = ui.menu().props("no-parent-event")
        with menu:
            ui.label(t("Site Selection")).classes("text-sm text-secondary q-mb-xs")

            with ui.row().classes("gap-2"):

                def _select_all() -> None:
                    for cb in site_cbs.values():
                        cb.set_value(True)

                def _clear_all() -> None:
                    for cb in site_cbs.values():
                        cb.set_value(False)

                ui.button(t("Select All"), on_click=_select_all).props("dense")
                ui.button(t("Clear"), on_click=_clear_all).props("dense")

            ui.separator()

            with (
                ui.scroll_area().classes("w-[300px] max-h-[260px] q-mt-xs"),
                ui.column().classes("gap-1"),
            ):
                selected = set(state.get("sites") or [])
                for key, label in SEARCH_SUPPORT_SITES.items():
                    site_cbs[key] = ui.checkbox(label, value=(key in selected))

            ui.separator()
            ui.label(t("Advanced Settings")).classes("text-sm text-secondary q-mt-sm")

            psl_in = (
                ui.number(
                    t("Per-site Limit"),
                    value=state["per_site_limit"],
                    min=1,
                    step=1,
                )
                .without_auto_validation()
                .classes("w-[180px]")
            )
            timeout_in = (
                ui.number(
                    t("Timeout (seconds)"),
                    value=state["timeout"],
                    format="%.1f",
                    min=0.1,
                    step=0.1,
                )
                .without_auto_validation()
                .classes("w-[180px]")
            )

    settings_btn.on("click", lambda: menu.open())

    def _get_sites() -> list[str] | None:
        chosen = [k for k, cb in site_cbs.items() if bool(cb.value)]
        return chosen or None

    def _get_psl() -> int:
        val = _coerce_psl(psl_in)
        state["per_site_limit"] = val
        return val

    def _get_timeout() -> float:
        val = _coerce_timeout(timeout_in)
        state["timeout"] = val
        return val

    return _get_sites, _get_psl, _get_timeout


@ui.page("/")  # type: ignore[misc]
def page_search() -> None:
    navbar("search")
    setup_dialog()

    state = _get_state()

    # ---------- Outer container ----------
    with ui.column().classes("w-full max-w-screen-lg min-w-[320px] mx-auto gap-4"):
        # ---------- Sticky toolbar ----------
        with ui.card().props("flat bordered").classes(
            "w-full sticky top-0 z-10 backdrop-blur"
        ):
            with ui.row().classes("items-center gap-2 w-full flex-wrap"):
                get_sites, get_psl, get_timeout = _build_settings_dropdown(state)

                query_in = (
                    ui.input(t("Enter keyword"), value=state["query"])
                    .props("outlined dense clearable autocomplete=off")
                    .classes("min-w-[260px] grow")
                )

                search_btn = ui.button(t("Search"), color="primary").props("unelevated")
                ui.button(t("Stop"), on_click=lambda: _cancel_current(state)).props(
                    "outline"
                )

            with ui.row().classes("items-center gap-3 w-full q-mt-xs flex-wrap"):
                sort_key_labels = {
                    "priority": t("Priority"),
                    "site": t("Site"),
                    "title": t("Title"),
                    "author": t("Author"),
                }
                sort_key_sel = (
                    ui.select(
                        sort_key_labels,
                        value=state["sort_key"],
                        label=t("Sort"),
                        with_input=False,
                    )
                    .props("outlined dense")
                    .classes("w-[180px]")
                )

                sort_order_sel = ui.toggle(
                    {"asc": t("Ascending"), "desc": t("Descending")},
                    value=state["sort_order"],
                ).props("dense")

                def _on_sort_change(_: Any = None) -> None:
                    state["sort_key"] = sort_key_sel.value or "priority"
                    state["sort_order"] = sort_order_sel.value or "desc"
                    _apply_sort(state)
                    state["page"] = 1
                    render_results.refresh()

                sort_key_sel.on_value_change(_on_sort_change)
                sort_order_sel.on_value_change(_on_sort_change)

        # ---------- Status ----------
        status_area = ui.row().classes(
            "items-center gap-2 my-2 w-full text-sm text-caption"
        )

        # ---------- Results + pager ----------
        list_area = ui.column().classes("w-full gap-3")
        pager_area = ui.row().classes("items-center justify-center w-full q-mt-md")

    @ui.refreshable  # type: ignore[misc]
    def render_status() -> None:
        status_area.clear()
        with status_area:
            if state.get("searching"):
                ui.icon("hourglass_top").classes("text-secondary")
                ui.label(t("Searching (results will appear progressively)...")).classes(
                    "text-caption"
                )
            total = len(state.get("results") or [])
            if total > 0:
                ui.label(
                    t("Currently retrieved {total} results").format(total=total)
                ).classes("text-caption")

    def _render_skeleton_card() -> None:
        with ui.card().props("flat bordered").classes("w-full h-[120px] animate-pulse"):
            pass

    @ui.refreshable  # type: ignore[misc]
    def render_results() -> None:
        list_area.clear()
        pager_area.clear()

        results: list[SearchResult] = state["results"]
        total = len(results)
        page_size = int(state["page_size"])
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = max(1, min(int(state["page"]), total_pages))
        state["page"] = page

        start = (page - 1) * page_size
        end = min(total, start + page_size)
        current = results[start:end]

        if total > 0:
            tip = t("Total {total} results (page {page}/{pages})").format(
                total=total, page=page, pages=total_pages
            )
            with list_area:
                ui.label(tip).classes("text-sm text-caption")
                for r in current:
                    _render_result_row(r)
        elif state.get("searching"):
            with list_area:
                for _ in range(3):
                    _render_skeleton_card()
        else:
            pass

        if total_pages > 1:

            def _on_page_change(e: ValueChangeEventArguments) -> None:
                try:
                    state["page"] = int(e.value or 1)
                except Exception:
                    state["page"] = 1
                render_results.refresh()

            with pager_area:
                ui.pagination(
                    1,  # min
                    total_pages,  # max
                    direction_links=True,
                    value=page,
                    on_change=_on_page_change,
                ).props(f"max-pages={_PAGER_WIDTH} boundary-numbers ellipses")

    def _cancel_current(st: dict[str, Any]) -> None:
        task: asyncio.Task[Any] | None = st.get("search_task")
        if task and not task.done():
            task.cancel()
        st["search_task"] = None
        st["searching"] = False
        render_status.refresh()

    async def _run_stream(
        q: str, sites: list[str] | None, per_site_limit: int, timeout_val: float
    ) -> None:
        try:
            # show loading state
            state["searching"] = True
            search_btn.props("loading")
            render_status.refresh()

            # clear existing results and reset pagination
            state["results"] = []
            state["page"] = 1
            render_results.refresh()

            async with aclosing(
                search_stream(
                    keyword=q,
                    sites=sites,
                    per_site_limit=per_site_limit,
                    timeout=timeout_val,
                )
            ) as stream:
                async for chunk in stream:
                    if not chunk:
                        continue
                    state["results"].extend(chunk)
                    _apply_sort(state)
                    render_status.refresh()
                    render_results.refresh()

        except asyncio.CancelledError:
            # cancellation when user starts a new search or presses Stop
            pass
        finally:
            state["searching"] = False
            search_btn.props(remove="loading")
            render_status.refresh()

    async def do_search() -> None:
        q = (query_in.value or "").strip()
        if not q:
            ui.notify(t("Please enter a keyword"), type="warning")
            return

        # Cancel any previous search
        _cancel_current(state)

        # persist current settings
        state["query"] = q
        state["sites"] = get_sites()
        per_site_limit = get_psl()
        timeout_val = get_timeout()

        # kick off streaming search as a background task
        task = asyncio.create_task(
            _run_stream(q, state["sites"], per_site_limit, timeout_val)
        )
        state["search_task"] = task

    def _on_key(e: KeyEventArguments) -> None:
        if not e.action.keyup:
            return

        total = len(state["results"])
        if total == 0:
            return
        page_size = int(state["page_size"])
        total_pages = max(1, (total + page_size - 1) // page_size)
        page = state["page"]

        if e.key == "ArrowLeft" and page > 1:
            state["page"] -= 1
            render_results.refresh()
        elif e.key == "ArrowRight" and page < total_pages:
            state["page"] += 1
            render_results.refresh()

    search_btn.on("click", do_search)
    query_in.on("keydown.enter", do_search)
    ui.keyboard(on_key=_on_key)

    # initial render
    render_status()
    render_results()

    # clean up state on disconnect to avoid leaks
    with suppress(Exception):
        ui.context.client.on_disconnect(_cleanup_state)
