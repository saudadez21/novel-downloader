#!/usr/bin/env python3
"""
novel_downloader.web.pages.search
---------------------------------

Search UI with a settings dropdown, persistent state, and paginated results.
"""

from __future__ import annotations

import contextlib
from collections.abc import Callable
from math import ceil
from typing import Any

from nicegui import ui
from nicegui.elements.number import Number
from nicegui.events import ValueChangeEventArguments

from novel_downloader.core import search
from novel_downloader.models import SearchResult
from novel_downloader.web.components import navbar
from novel_downloader.web.services import manager, setup_dialog

_SUPPORT_SITES = {
    "aaatxt": "3A电子书",
    "biquge": "笔趣阁",
    "dxmwx": "大熊猫文学网",
    "eightnovel": "无限轻小说",
    "esjzone": "ESJ Zone",
    "hetushu": "和图书",
    "i25zw": "25中文网",
    "ixdzs8": "爱下电子书",
    "jpxs123": "精品小说网",
    "piaotia": "飘天文学网",
    "qbtr": "全本同人小说",
    "qianbi": "铅笔小说",
    "quanben5": "全本小说网",
    "shuhaige": "书海阁小说网",
    "tongrenquan": "同人圈",
    "ttkan": "天天看小说",
    # "wanbengo": "完本神站",
    "xiaoshuowu": "小说屋",
    "xiguashuwu": "西瓜书屋",
    "xs63b": "小说路上",
    # "xshbook": "小说虎",
}

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
        }
    return _STATE[cid]


def _cleanup_state() -> None:
    cid = ui.context.client.id
    _STATE.pop(cid, None)


def _coerce_timeout(inp: Number) -> float:
    v = inp.value
    try:
        v = float(v)
        if v <= 0:
            raise ValueError
    except (TypeError, ValueError):
        ui.notify("超时需 > 0 秒，已重置为 10.0", type="warning")
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
        ui.notify("单站条数上限需为正整数，已重置为 5", type="warning")
        v = _DEFAULT_SITE_LIMIT
    inp.set_value(v)
    inp.sanitize()
    return int(v)


def _render_placeholder_cover() -> None:
    with ui.element("div").classes(
        "w-[72px] h-[96px] bg-grey-3 rounded-md flex items-center " "justify-center"
    ):
        ui.icon("book").classes("text-grey-6 text-3xl")


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
                f"{r['author']} · {r['word_count']} · 更新于 {r['update_date']}"
            ).classes("text-xs text-grey-6")
            ui.label(r["latest_chapter"]).classes("text-sm text-grey-7")
            ui.label(f"{r['site']} · ID: {r['book_id']}").classes("text-xs text-grey-5")

        async def _add_task() -> None:
            title = r["title"]
            ui.notify(f"已添加任务：{title}")
            await manager.add_task(title=title, site=r["site"], book_id=r["book_id"])

        ui.button("下载", color="primary", on_click=_add_task).props("unelevated")


def _build_settings_dropdown(
    state: dict[str, Any],
) -> tuple[Callable[[], list[str] | None], Callable[[], int], Callable[[], float]]:
    """
    Create settings button + anchored menu with initial values from state.

    Returns a tuple of getter functions:
      - get_sites(): list of site keys, or None if none selected
      - get_psl(): per-site limit (int)
      - get_timeout(): timeout (float)
    """
    site_cbs: dict[str, Any] = {}

    settings_btn = ui.button("设置").props("outline icon=settings")
    with settings_btn:
        menu = ui.menu().props("no-parent-event")
        with menu:
            ui.label("站点选择").classes("text-sm text-grey-7 q-mb-xs")

            with ui.row().classes("gap-2"):

                def _select_all() -> None:
                    for cb in site_cbs.values():
                        cb.set_value(True)

                def _clear_all() -> None:
                    for cb in site_cbs.values():
                        cb.set_value(False)

                ui.button("全选", on_click=_select_all).props("dense")
                ui.button("清空", on_click=_clear_all).props("dense")

            ui.separator()

            with (
                ui.scroll_area().classes("w-[300px] max-h-[260px] q-mt-xs"),
                ui.column().classes("gap-1"),
            ):
                selected = set(state.get("sites") or [])
                for key, label in _SUPPORT_SITES.items():
                    site_cbs[key] = ui.checkbox(label, value=(key in selected))

            ui.separator()
            ui.label("高级设置").classes("text-sm text-grey-7 q-mt-sm")

            psl_in = (
                ui.number(
                    "单站条数上限",
                    value=state["per_site_limit"],
                    min=1,
                    step=1,
                )
                .without_auto_validation()
                .classes("w-[180px]")
            )
            timeout_in = (
                ui.number(
                    "超时(秒)",
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
    ui.label("搜索页面").classes("text-lg")
    setup_dialog()

    state = _get_state()

    # settings (left) + query (middle) + search (right)
    with ui.row().classes("items-center gap-2 my-2 w-full"):
        get_sites, get_psl, get_timeout = _build_settings_dropdown(state)

        query_in = (
            ui.input("输入关键字", value=state["query"])
            .props("outlined dense clearable")
            .classes("min-w-[320px] grow")
        )

        search_btn = ui.button("搜索", color="primary").props("unelevated")

    # results & pagination container
    list_area = ui.column().classes("w-full")
    pager_area = ui.row().classes("items-center justify-center w-full q-mt-md")

    @ui.refreshable  # type: ignore[misc]
    def render_results() -> None:
        list_area.clear()
        pager_area.clear()

        results: list[SearchResult] = state["results"]
        total = len(results)
        page_size = int(state["page_size"])
        total_pages = max(1, ceil(total / page_size))
        page = max(1, min(int(state["page"]), total_pages))
        state["page"] = page

        start = (page - 1) * page_size
        end = min(total, start + page_size)
        current = results[start:end]

        tip = (
            f"共 {total} 条结果（第 {page}/{total_pages} 页）"
            if state["sites"]
            else f"共 {total} 条结果（第 {page}/{total_pages} 页，已搜索全部站点）"
        )

        with list_area:
            ui.label(tip).classes("text-sm text-grey-7")
            with ui.column().classes("w-full gap-2"):
                for r in current:
                    _render_result_row(r)

        # pagination (only show if more than 1 page)
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

    async def do_search() -> None:
        q = (query_in.value or "").strip()
        if not q:
            ui.notify("请输入关键词", type="warning")
            return

        state["query"] = q
        state["sites"] = get_sites()
        per_site_limit = get_psl()
        timeout_val = get_timeout()

        # perform search
        results = await search(
            keyword=q,
            sites=state["sites"],
            limit=None,  # show all
            per_site_limit=per_site_limit,
            timeout=timeout_val,
        )
        state["results"] = results
        state["page"] = 1
        render_results.refresh()

    search_btn.on("click", do_search)
    query_in.on("keydown.enter", do_search)

    # initial render
    render_results()

    # clean up state on disconnect to avoid leaks
    with contextlib.suppress(Exception):
        ui.context.client.on_disconnect(_cleanup_state)
