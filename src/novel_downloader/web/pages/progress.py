#!/usr/bin/env python3
"""
novel_downloader.web.pages.progress
-----------------------------------

Layout for active/history tasks with compact cards and status chips.
"""


from nicegui import ui

from novel_downloader.web.components import navbar
from novel_downloader.web.services import DownloadTask, Status, manager, setup_dialog


def _status_chip(status: Status) -> None:
    label_map = {
        "queued": "已排队",
        "running": "运行中",
        "completed": "完成",
        "cancelled": "已取消",
        "failed": "失败",
    }
    color_map = {
        "queued": "warning",
        "running": "primary",
        "completed": "positive",
        "cancelled": "grey-6",
        "failed": "negative",
    }
    ui.chip(label_map[status]).props(
        f"outline color={color_map[status]} dense"
    ).classes("q-ml-sm")


def _meta_row(label: str, value: str) -> None:
    with ui.row().classes("items-center justify-between text-xs text-grey-7 w-full"):
        ui.label(label)
        ui.label(value)


def _progress_block(t: DownloadTask) -> None:
    # progress or summary depending on state
    if t.status == "running":
        if t.chapters_total <= 0:
            label_text = f"{t.chapters_done}/? · 正在获取总章节..."
            ui.linear_progress().props("indeterminate striped").classes("w-full")
            ui.label(label_text).classes("text-xs text-grey-7")
        else:
            ui.linear_progress(value=t.progress()).props("instant-feedback").classes(
                "w-full"
            )
            ui.label(f"{t.chapters_done}/{t.chapters_total} · running").classes(
                "text-xs text-grey-7"
            )
    else:
        suffix = {"completed": "完成", "cancelled": "已取消", "failed": "失败"}.get(
            t.status, ""
        )
        if t.chapters_total > 0:
            ui.label(f"{t.chapters_done}/{t.chapters_total} · {suffix}").classes(
                "text-xs text-grey-7"
            )
        else:
            ui.label(f"{t.chapters_done}/? · {suffix}").classes("text-xs text-grey-7")

        if t.status == "completed" and t.exported_paths:
            with ui.row().classes("w-full gap-2 mt-1"):
                for key, p in t.exported_paths.items():
                    url = f"/download/{p.name}?v={t.task_id}"
                    ui.button(key, on_click=lambda e, url=url: ui.download(url)).props(
                        "outline size=sm"
                    )


def _task_card(t: DownloadTask, *, active: bool) -> None:
    with ui.card().classes("w-full"):
        # header
        with ui.row().classes("items-center justify-between w-full"):
            with ui.row().classes("items-center gap-2"):
                ui.label(t.title).classes("text-sm font-medium")
                _status_chip(t.status)
            if active and t.status in ("running", "queued"):

                async def cancel_this(tid: str = t.task_id) -> None:
                    ok = await manager.cancel_task(tid)
                    ui.notify(
                        f"任务 {tid[:8]} {'已取消' if ok else '取消失败'}",
                        color=("primary" if ok else "negative"),
                    )

                ui.button("取消", on_click=cancel_this)
            else:
                ui.button(
                    "取消",
                    on_click=lambda: ui.notify("任务已结束，无法取消"),
                ).props("disable")

        # meta grid
        with ui.column().classes("w-full gap-1 mt-2"):
            _meta_row("站点", t.site)
            _meta_row("书号", t.book_id)
            if t.status == "failed" and t.error:
                with ui.row().classes("items-start justify-between w-full"):
                    ui.label("错误").classes("text-xs text-grey-7")
                    ui.label(t.error).classes("text-xs text-negative q-ml-md")

        # progress / summary
        with ui.column().classes("w-full mt-2"):
            _progress_block(t)


@ui.page("/progress")  # type: ignore[misc]
def page_progress() -> None:
    navbar("progress")
    ui.label("正在下载 / 历史记录").classes("text-lg")
    setup_dialog()

    @ui.refreshable  # type: ignore[misc]
    def section() -> None:
        s = manager.snapshot()

        # Active first
        ui.label("运行中 / 等待中").classes("text-base mt-2")
        with ui.card().classes("w-full"):
            running = s["running"]
            pending = s["pending"]
            if not running and not pending:
                ui.label("暂无").classes("text-sm text-grey-6")
            else:
                if running:
                    _task_card(running, active=True)
                for t in pending:
                    _task_card(t, active=True)

        # History next
        ui.label("已完成 / 已取消 / 失败").classes("text-base mt-4")
        with ui.card().classes("w-full"):
            if not s["completed"]:
                ui.label("暂无").classes("text-sm text-grey-6")
            else:
                for t in s["completed"]:
                    _task_card(t, active=False)

    # periodic refresh
    ui.timer(0.5, section.refresh)
    section()
