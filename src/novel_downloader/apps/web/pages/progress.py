#!/usr/bin/env python3
"""
novel_downloader.apps.web.pages.progress
----------------------------------------

Layout for active/history tasks with compact cards and status chips.
"""

from nicegui import ui

from novel_downloader.infra.i18n import t

from ..components import navbar
from ..services import (
    DownloadTask,
    Status,
    manager,
    setup_dialog,
)


def _status_chip(status: Status) -> None:
    label_map = {
        "queued": t("Queued"),
        "running": t("Downloading"),
        "exporting": t("Exporting"),
        "completed": t("Completed"),
        "cancelled": t("Cancelled"),
        "failed": t("Failed"),
    }
    color_map = {
        "queued": "warning",
        "running": "primary",
        "exporting": "secondary",
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


def _progress_block(tsk: DownloadTask) -> None:
    # progress or summary depending on state
    if tsk.status == "running":
        if tsk.chapters_total <= 0:
            ui.linear_progress().props("indeterminate striped").classes("w-full")
            ui.label(
                t("{done}/? · Fetching total chapters...").format(
                    done=tsk.chapters_done
                )
            ).classes("text-xs text-grey-7")
        else:
            ui.linear_progress(value=tsk.progress()).props("instant-feedback").classes(
                "w-full"
            )
            ui.label(
                t("{done}/{total} · Running").format(
                    done=tsk.chapters_done, total=tsk.chapters_total
                )
            ).classes("text-xs text-grey-7")

    elif tsk.status == "exporting":
        ui.linear_progress().props("indeterminate striped").classes("w-full")
        ui.label(t("Exporting...")).classes("text-xs text-grey-7")

    else:
        suffix = {
            "completed": t("Completed"),
            "cancelled": t("Cancelled"),
            "failed": t("Failed"),
        }.get(tsk.status, "")

        if tsk.chapters_total > 0:
            ui.label(f"{tsk.chapters_done}/{tsk.chapters_total} · {suffix}").classes(
                "text-xs text-grey-7"
            )
        else:
            ui.label(f"{tsk.chapters_done}/? · {suffix}").classes("text-xs text-grey-7")

        if tsk.status == "completed" and tsk.exported_paths:
            with ui.row().classes("w-full gap-2 mt-1"):
                for key, p in tsk.exported_paths.items():
                    url = f"/downloads/{p.name}?v={tsk.task_id}"
                    ui.button(key, on_click=lambda e, url=url: ui.download(url)).props(
                        "outline size=sm"
                    )


def _task_card(tsk: DownloadTask, *, active: bool) -> None:
    with ui.card().classes("w-full"):
        # Header
        with ui.row().classes("items-center justify-between w-full"):
            with ui.row().classes("items-center gap-2"):
                ui.label(tsk.title).classes("text-sm font-medium")
                _status_chip(tsk.status)

            # Cancel button (active tasks only)
            if active and tsk.status in ("running", "queued"):

                async def cancel_this(tid: str = tsk.task_id) -> None:
                    ok = await manager.cancel_task(tid)
                    ui.notify(
                        f'Task {tid[:8]} {t("Cancelled") if ok else t("Cancel failed")}',  # noqa: E501
                        color=("primary" if ok else "negative"),
                    )

                ui.button(t("Cancel"), on_click=cancel_this).props("outline")
            else:
                ui.button(
                    t("Cancel"),
                    on_click=lambda: ui.notify(
                        t("Task has ended and cannot be cancelled")
                    ),
                ).props("disable outline")

        # Meta grid
        with ui.column().classes("w-full gap-1 mt-2"):
            _meta_row(t("Site"), tsk.site)
            _meta_row(t("Book ID"), tsk.book_id)
            if tsk.status == "failed" and tsk.error:
                with ui.row().classes("items-start justify-between w-full"):
                    ui.label(t("Error")).classes("text-xs text-grey-7")
                    ui.label(tsk.error).classes("text-xs text-negative q-ml-md")

        # Progress / summary
        with ui.column().classes("w-full mt-2"):
            _progress_block(tsk)


@ui.page("/progress")  # type: ignore[misc]
def page_progress() -> None:
    navbar("progress")
    setup_dialog()

    with ui.column().classes("w-full max-w-screen-lg min-w-[320px] mx-auto gap-4"):

        @ui.refreshable  # type: ignore[misc]
        def section() -> None:
            s = manager.snapshot()

            # Active section
            with ui.card().classes("w-full"):
                ui.label(t("Running / Queued")).classes("text-base")
                running = s["running"]
                pending = s["pending"]
                if not running and not pending:
                    ui.label(t("None")).classes("text-sm text-grey-6")
                else:
                    for tsk in running:
                        _task_card(tsk, active=True)
                    for tsk in pending:
                        _task_card(tsk, active=True)

            # History section
            with ui.card().classes("w-full"):
                ui.label(t("Completed / Cancelled / Failed")).classes("text-base")
                if not s["completed"]:
                    ui.label(t("None")).classes("text-sm text-grey-6")
                else:
                    for tsk in s["completed"]:
                        _task_card(tsk, active=False)

        # periodic refresh
        ui.timer(0.5, section.refresh)
        section()
