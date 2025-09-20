#!/usr/bin/env python3
"""
novel_downloader.web.pages.search
---------------------------------

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

from novel_downloader.core.searchers import search_stream
from novel_downloader.models import SearchResult
from novel_downloader.web.components import navbar
from novel_downloader.web.services import manager, setup_dialog

_SUPPORT_SITES = {
    "aaatxt": "3A电子书",
    "b520": "笔趣阁",
    "biquge5": "笔趣阁",
    "biquguo": "笔趣阁小说网",
    "bxwx9": "笔下文学网",
    "ciluke": "思路客",
    "dxmwx": "大熊猫文学网",
    "esjzone": "ESJ Zone",
    "fsshu": "笔趣阁",
    "hetushu": "和图书",
    "i25zw": "25中文网",
    "ixdzs8": "爱下电子书",
    "jpxs123": "精品小说网",
    "ktshu": "八一中文网",
    "laoyaoxs": "老幺小说网",
    "mangg_net": "追书网.net",
    "n8novel": "无限轻小说",
    "n23ddw": "顶点小说网",
    "n23qb": "铅笔小说",
    "n37yq": "三七轻小说",
    "n37yue": "37阅读网",
    "n71ge": "新吾爱文学",
    "piaotia": "飘天文学网",
    "qbtr": "全本同人小说",
    "qidian": "起点中文网",
    "quanben5": "全本小说网",
    "shuhaige": "书海阁小说网",
    "tongrenquan": "同人圈",
    "trxs": "同人小说网",
    "ttkan": "天天看小说",
    "wanbengo": "完本神站",
    # "xiaoshuoge": "小说屋",
    "xiguashuwu": "西瓜书屋",
    # "xs63b": "小说路上",
    "xshbook": "小说虎",
    "yodu": "有度中文网",
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
        ui.notify("单站条数上限需为正整数，已重置为 30", type="warning")
        v = _DEFAULT_SITE_LIMIT
    inp.set_value(v)
    inp.sanitize()
    return int(v)


def _render_placeholder_cover() -> None:
    with ui.element("div").classes(
        "w-[72px] h-[96px] bg-grey-3 rounded-md flex items-center justify-center"
    ):
        ui.icon("book").classes("text-grey-6 text-3xl")


def _site_label(site_key: str) -> str:
    return _SUPPORT_SITES.get(site_key, site_key)


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
                f"{r['author']} · {r['word_count']} · 更新于 {r['update_date']}"
            ).classes("text-xs text-grey-6")
            ui.label(r["latest_chapter"]).classes("text-sm text-grey-7")

            ui.label(f"{_site_label(r['site'])} · ID: {r['book_id']}").classes(
                "text-xs text-grey-5"
            )

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
      * get_sites(): list of site keys, or None if none selected
      * get_psl(): per-site limit (int)
      * get_timeout(): timeout (float)
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
    setup_dialog()

    state = _get_state()

    # ---------- Outer container ----------
    with ui.column().classes("w-full max-w-screen-lg min-w-[320px] mx-auto gap-4"):
        # ---------- Sticky toolbar ----------
        with ui.card().classes(
            "w-full sticky top-0 z-10 backdrop-blur bg-white/70 border-0 shadow-sm"
        ):
            with ui.row().classes("items-center gap-2 w-full"):
                get_sites, get_psl, get_timeout = _build_settings_dropdown(state)

                query_in = (
                    ui.input("输入关键字", value=state["query"])
                    .props("outlined dense clearable")
                    .classes("min-w-[320px] grow")
                )

                search_btn = ui.button("搜索", color="primary").props("unelevated")
                ui.button("停止", on_click=lambda: _cancel_current(state)).props(
                    "outline"
                )

            with ui.row().classes("items-center gap-3 w-full q-mt-xs"):
                sort_key_labels = {
                    "priority": "优先级",
                    "site": "站点",
                    "title": "标题",
                    "author": "作者",
                }
                sort_key_sel = (
                    ui.select(
                        sort_key_labels,
                        value=state["sort_key"],
                        label="排序",
                        with_input=False,
                    )
                    .props("outlined dense")
                    .classes("w-[180px]")
                )

                sort_order_sel = (
                    ui.toggle(
                        {"asc": "升序", "desc": "降序"},
                        value=state["sort_order"],
                    )
                    .props("dense")
                    .classes("")
                )

                def _on_sort_change(_: Any = None) -> None:
                    state["sort_key"] = sort_key_sel.value or "priority"
                    state["sort_order"] = sort_order_sel.value or "desc"
                    _apply_sort(state)
                    state["page"] = 1
                    render_results.refresh()

                sort_key_sel.on_value_change(_on_sort_change)
                sort_order_sel.on_value_change(_on_sort_change)

        # ---------- Status ----------
        status_area = ui.row().classes("items-center gap-2 my-2 w-full")

        # ---------- Results + pager ----------
        list_area = ui.column().classes("w-full gap-2")
        pager_area = ui.row().classes("items-center justify-center w-full q-mt-md")

    @ui.refreshable  # type: ignore[misc]
    def render_status() -> None:
        status_area.clear()
        with status_area:
            if state.get("searching"):
                ui.icon("hourglass_top").classes("text-grey-6")
                ui.label("正在搜索（结果将陆续显示）...").classes("text-sm text-grey-7")
            total = len(state.get("results") or [])
            if total > 0:
                ui.label(f"当前已获取 {total} 条结果").classes("text-sm text-grey-7")

    def _render_skeleton_card() -> None:
        with ui.card().classes("w-full h-[120px] bg-grey-2 animate-pulse"):
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
            tip = (
                f"共 {total} 条结果（第 {page}/{total_pages} 页）"
                if state["sites"]
                else f"共 {total} 条结果（第 {page}/{total_pages} 页，已搜索全部站点）"
            )
            with list_area:
                ui.label(tip).classes("text-sm text-grey-7")
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
            ui.notify("请输入关键词", type="warning")
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
