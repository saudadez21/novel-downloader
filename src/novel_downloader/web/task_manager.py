#!/usr/bin/env python3
"""
novel_downloader.web.task_manager
---------------------------------

"""

from __future__ import annotations

import asyncio
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from nicegui import ui

from novel_downloader.config import ConfigAdapter
from novel_downloader.core import (
    FetcherProtocol,
    get_downloader,
    get_exporter,
    get_fetcher,
    get_parser,
)
from novel_downloader.models import (
    BookConfig,
    DownloaderConfig,
    LoginField,
)
from novel_downloader.utils.cookies import parse_cookies
from novel_downloader.web import state as web_state

Status = Literal["queued", "running", "completed", "cancelled", "failed"]


@dataclass
class DownloadTask:
    title: str
    site: str
    book_id: str
    created_ts: float = field(default_factory=time.time)
    task_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    client_id: str | None = None

    # runtime state
    status: Status = "queued"
    chapters_total: int = 0
    chapters_done: int = 0
    error: str | None = None
    _cancel_event: asyncio.Event = field(default_factory=asyncio.Event, repr=False)

    def progress(self) -> float:
        if self.chapters_total <= 0:
            return 0.0
        return self.chapters_done / self.chapters_total

    def cancel(self) -> None:
        self._cancel_event.set()


class TaskManager:
    """
    Single-worker FIFO queue.
    """

    def __init__(self, settings: dict[str, Any]):
        self.settings = settings
        self.pending: list[DownloadTask] = []
        self.running: DownloadTask | None = None
        self.completed: list[DownloadTask] = []
        self._new_item = asyncio.Event()
        self._worker_task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

    # ---------- public API ----------
    async def add_task(self, *, title: str, site: str, book_id: str) -> DownloadTask:
        try:
            client_id = ui.context.client.id
        except Exception:
            client_id = None

        t = DownloadTask(title=title, site=site, book_id=book_id, client_id=client_id)
        async with self._lock:
            self.pending.append(t)
            self._new_item.set()
            if not self._worker_task or self._worker_task.done():
                self._worker_task = asyncio.create_task(self._worker())
        return t

    async def cancel_task(self, task_id: str) -> bool:
        async with self._lock:
            # cancel pending
            for i, t in enumerate(self.pending):
                if t.task_id == task_id:
                    t.status = "cancelled"
                    self.completed.insert(0, t)
                    del self.pending[i]
                    return True
            # cancel running
            if self.running and self.running.task_id == task_id:
                self.running.cancel()
                return True
        return False

    def snapshot(self) -> dict[str, Any]:
        return {
            "running": self.running,
            "pending": list(self.pending),
            "completed": list(self.completed),
        }

    # ---------- internals ----------
    async def _worker(self) -> None:
        while True:
            await self._new_item.wait()
            self._new_item.clear()
            while True:
                async with self._lock:
                    if self.running is not None:
                        break
                    if not self.pending:
                        break
                    task = self.pending.pop(0)
                    self.running = task

                await self._run_task(task)

                async with self._lock:
                    self.completed.insert(0, task)
                    self.running = None

    async def _run_task(self, task: DownloadTask) -> None:
        task.status = "running"
        try:
            adapter = ConfigAdapter(config=self.settings, site=task.site)
            downloader_cfg = adapter.get_downloader_config()
            fetcher_cfg = adapter.get_fetcher_config()
            parser_cfg = adapter.get_parser_config()
            exporter_cfg = adapter.get_exporter_config()

            parser = get_parser(task.site, parser_cfg)
            exporter = get_exporter(task.site, exporter_cfg)

            async with get_fetcher(task.site, fetcher_cfg) as fetcher:
                # login if required
                if getattr(downloader_cfg, "login_required", False):
                    loaded = await fetcher.load_state()
                    if not loaded or not getattr(fetcher, "is_logged_in", False):
                        login_ok = await self._handle_login(
                            fetcher, downloader_cfg, task.client_id
                        )
                        if not login_ok:
                            task.status = "failed"
                            task.error = "登录失败或已取消"
                            return
                        await fetcher.save_state()

                downloader = get_downloader(
                    fetcher=fetcher,
                    parser=parser,
                    site=task.site,
                    config=downloader_cfg,
                )

                async def _progress_hook(done: int, total: int) -> None:
                    if total and (
                        task.chapters_total <= 0 or total > task.chapters_total
                    ):
                        task.chapters_total = total
                    task.chapters_done = done
                    # allow cooperative cancel from UI
                    if task._cancel_event.is_set():
                        raise asyncio.CancelledError()

                book_cfg: BookConfig = {"book_id": task.book_id}
                try:
                    await downloader.download(
                        book_cfg,
                        progress_hook=_progress_hook,
                    )
                except asyncio.CancelledError:
                    task.status = "cancelled"
                    return

                await asyncio.to_thread(exporter.export, task.book_id)

                if getattr(downloader_cfg, "login_required", False) and getattr(
                    fetcher, "is_logged_in", False
                ):
                    await fetcher.save_state()

                task.status = "completed"

        except Exception as e:
            task.status = "failed"
            task.error = str(e)

    async def _handle_login(
        self,
        fetcher: FetcherProtocol,
        downloader_cfg: DownloaderConfig,
        client_id: str | None,
    ) -> bool:
        """Prompt UI login; supports text/password/cookie fields."""
        fields: list[LoginField] = getattr(fetcher, "login_fields", []) or []

        cfg_dict: dict[str, str] = {}
        try:
            cfg_dict = asdict(downloader_cfg)
        except Exception:
            try:
                cfg_dict = dict(downloader_cfg)  # type: ignore
            except Exception:
                cfg_dict = {}

        portal = web_state.get_portal(client_id)
        if portal is None:
            return False

        fut: asyncio.Future[
            dict[str, Any] | None
        ] = asyncio.get_event_loop().create_future()
        inputs: dict[str, Any] = {}

        def _close_with_result(ok: bool) -> None:
            if fut.done():
                return
            if not ok:
                fut.set_result(None)
                dialog.close()
                return
            data: dict[str, Any] = {}
            for fld in fields:
                val = inputs[fld.name].value
                if (not val) and getattr(fld, "default", None):
                    val = fld.default
                if getattr(fld, "type", "") == "cookie" and isinstance(val, str):
                    val = parse_cookies(val)
                data[fld.name] = val
            fut.set_result(data)
            dialog.close()

        with portal:
            with ui.dialog() as dialog, ui.card().classes("w-[540px] max-w-full"):
                ui.label("需要登录").classes("text-base font-medium")
                ui.separator()
                with ui.column().classes("w-full gap-2"):
                    for fld in fields:
                        prefill = (cfg_dict.get(fld.name, "") or "").strip()
                        label = f"{fld.label} ({fld.name})" if fld.label else fld.name
                        hint = (
                            getattr(fld, "description", None)
                            or getattr(fld, "placeholder", None)
                            or ""
                        )
                        if getattr(fld, "type", "") == "password":
                            el = ui.input(
                                label,
                                password=True,
                                password_toggle_button=True,
                                value=prefill,
                            )
                        elif getattr(fld, "type", "") == "cookie":
                            el = ui.textarea(label, value=prefill).props("rows=3")
                        else:
                            el = ui.input(label, value=prefill)
                        if hint:
                            el.props(f"hint={hint} persistent-hint")
                        inputs[fld.name] = el
                with ui.row().classes("justify-end w-full mt-2"):
                    ui.button("取消", on_click=lambda: _close_with_result(False))
                    ui.button(
                        "登录",
                        color="primary",
                        on_click=lambda: _close_with_result(True),
                    ).props("unelevated")

            dialog.open()
        values = await fut
        if values is None:
            return False
        ok = await fetcher.login(**values)
        return bool(ok)
