#!/usr/bin/env python3
"""
novel_downloader.web.pages.progress_page
----------------------------------------

"""

from nicegui import ui

from novel_downloader.web.layout import navbar
from novel_downloader.web.state import (
    register_portal,
    task_manager,
)
from novel_downloader.web.task_manager import DownloadTask


def _task_row(t: DownloadTask, active: bool) -> None:
    with ui.row().classes("items-center justify-between w-full"):
        with ui.column().classes("gap-0.5"):
            ui.label(t.title).classes("text-sm font-medium")
            meta = f"{t.site} | book_id={t.book_id}"
            if t.status == "failed" and t.error:
                meta += f" | 错误: {t.error}"
            ui.label(meta).classes("text-xs text-grey-6")

        with ui.row().classes("items-center gap-2"):
            if active and t.status in ("running", "queued"):

                async def cancel_this(tid: str = t.task_id) -> None:
                    await task_manager.cancel_task(tid)

                ui.button("取消", on_click=cancel_this)
            else:
                btn = ui.button(
                    "取消",
                    on_click=lambda: ui.notify("任务已结束，无法取消"),
                )
                btn.props("disable")

    # Progress display:
    if t.status == "running":
        if t.chapters_total <= 0:
            ui.linear_progress().props("indeterminate striped").classes("w-full mt-1")
            label_text = f"{t.chapters_done}/? · 正在获取总章节..."
            ui.label(label_text).classes("text-xs text-grey-7")
        else:
            ui.linear_progress(value=t.progress()).props("instant-feedback").classes(
                "w-full mt-1"
            )
            ui.label(f"{t.chapters_done}/{t.chapters_total} · running").classes(
                "text-xs text-grey-7"
            )

    elif t.status in ("completed", "cancelled", "failed"):
        # Small summary line, no progress bar for history
        suffix = (
            "完成"
            if t.status == "completed"
            else ("已取消" if t.status == "cancelled" else "失败")
        )
        if t.chapters_total > 0:
            ui.label(f"{t.chapters_done}/{t.chapters_total} · {suffix}").classes(
                "text-xs text-grey-7"
            )
        else:
            ui.label(f"{t.chapters_done}/? · {suffix}").classes("text-xs text-grey-7")

    ui.separator()


@ui.page("/progress")  # type: ignore[misc]
def render() -> None:
    navbar("progress")
    register_portal()
    ui.label("正在下载 / 历史记录").classes("text-lg")

    @ui.refreshable  # type: ignore[misc]
    def section() -> None:
        s = task_manager.snapshot()

        ui.label("已完成 / 已取消 / 失败").classes("text-base mt-2")
        with ui.card().classes("w-full"):
            if not s["completed"]:
                ui.label("暂无").classes("text-sm text-grey-6")
            else:
                for t in s["completed"]:
                    _task_row(t, active=False)

        ui.label("运行中 / 等待中").classes("text-base mt-4")
        with ui.card().classes("w-full"):
            running = s["running"]
            pending = s["pending"]
            if not running and not pending:
                ui.label("暂无").classes("text-sm text-grey-6")
            else:
                if running:
                    _task_row(running, active=False)
                for t in pending:
                    _task_row(t, active=True)

    ui.timer(0.5, section.refresh)
    section()
