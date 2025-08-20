#!/usr/bin/env python3
"""
novel_downloader.web.pages.search_page
--------------------------------------

"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from nicegui import ui

import novel_downloader.web.state
from novel_downloader.core import search
from novel_downloader.models import SearchResult
from novel_downloader.web.layout import navbar


@ui.page("/search")  # type: ignore[misc]
def _alias_search() -> None:
    render()


def render() -> None:
    navbar("search")
    ui.label("搜索页面").classes("text-lg")

    with ui.row().classes("items-center gap-2 my-2 w-full"):
        query_in = (
            ui.input("输入关键字")
            .props("outlined dense clearable")
            .classes("w-[420px]")  # noqa: E501
        )
        timeout_in = (
            ui.number("超时(秒)", value=10.0, format="%.1f", min=0.1, step=0.1)
            .without_auto_validation()
            .classes("w-[140px]")
        )
        search_btn = ui.button("搜索", color="primary").props("unelevated")

    def _coerce_timeout(_: Any = None) -> None:
        v = timeout_in.value
        try:
            v = float(v)
            if v <= 0:
                raise ValueError
        except (TypeError, ValueError):
            ui.notify("超时需 > 0 秒，已重置为 10.0", type="warning")
            v = 10.0
        timeout_in.set_value(v)
        timeout_in.sanitize()

    timeout_in.on("blur", _coerce_timeout)

    show_area = ui.column().classes("w-full")

    def make_add_handler(r: SearchResult) -> Callable[[], Awaitable[None]]:
        async def handler() -> None:
            title = r["title"]
            ui.notify(f"已添加任务：{title}")
            await novel_downloader.web.state.task_manager.add_task(
                title=title,
                site=r["site"],
                book_id=r["book_id"],
            )

        return handler

    def _render_placeholder_cover() -> None:
        with ui.element("div").classes(
            "w-[72px] h-[96px] bg-grey-3 rounded-md flex items-center justify-center"
        ):
            ui.icon("book").classes("text-grey-6 text-3xl")

    def _render_result_row(r: SearchResult) -> None:
        with (
            ui.card().classes("w-full"),
            ui.row().classes("items-start justify-between w-full gap-3"),
        ):
            cover = (r.get("cover_url") or "").strip()
            if cover.startswith("http://") or cover.startswith("https://"):
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
                ui.label(f"{r['site']} · ID: {r['book_id']}").classes(
                    "text-xs text-grey-5"
                )

            ui.button("下载", color="primary", on_click=make_add_handler(r)).props(
                "unelevated"
            )

    async def do_search() -> None:
        show_area.clear()
        q = (query_in.value or "").strip()
        if not q:
            ui.notify("请输入关键词", type="warning")
            return

        _coerce_timeout()
        timeout_val = float(timeout_in.value)

        results = await search(q, timeout=timeout_val)

        with show_area:
            ui.label(f"共 {len(results)} 条结果").classes("text-sm text-grey-7")
            with ui.column().classes("w-full gap-2"):
                for r in results:
                    _render_result_row(r)

    search_btn.on("click", do_search)
    query_in.on("keydown.enter", do_search)
