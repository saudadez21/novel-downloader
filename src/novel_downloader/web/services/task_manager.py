#!/usr/bin/env python3
"""
novel_downloader.web.services.task_manager
------------------------------------------

Single-worker FIFO task manager for download jobs
"""

import asyncio
import contextlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from novel_downloader.config import ConfigAdapter, load_config
from novel_downloader.core import (
    get_downloader,
    get_exporter,
    get_fetcher,
    get_parser,
)
from novel_downloader.models import (
    BookConfig,
    LoginField,
)
from novel_downloader.utils.cookies import parse_cookies

from .cred_broker import (
    REQUEST_TIMEOUT,
    cleanup_request,
    complete_request,
    create_cred_request,
)

Status = Literal["queued", "running", "completed", "cancelled", "failed"]


@dataclass
class DownloadTask:
    title: str
    site: str
    book_id: str

    # runtime state
    task_id: str = field(default_factory=lambda: uuid4().hex)
    status: Status = "queued"
    chapters_total: int = 0
    chapters_done: int = 0
    error: str | None = None
    exported_paths: dict[str, Path] | None = None

    _cancel_event: asyncio.Event = field(default_factory=asyncio.Event, repr=False)

    def progress(self) -> float:
        if self.chapters_total <= 0:
            return 0.0
        return self.chapters_done / self.chapters_total

    def cancel(self) -> None:
        self._cancel_event.set()
        self.status = "cancelled"

    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()


class TaskManager:
    """
    A cooperative, single-worker queue that executes download tasks in order.
    """

    def __init__(self) -> None:
        self.pending: list[DownloadTask] = []
        self.running: DownloadTask | None = None
        self.completed: list[DownloadTask] = []
        self._new_item = asyncio.Event()
        self._worker_task: asyncio.Task[None] | None = None
        self._lock = asyncio.Lock()

        self._settings = load_config()

    # ---------- public API ----------
    async def add_task(self, *, title: str, site: str, book_id: str) -> DownloadTask:
        """
        Enqueue a new task and ensure the worker is running; return the created task.
        """
        t = DownloadTask(title=title, site=site, book_id=book_id)
        async with self._lock:
            self.pending.append(t)
            self._new_item.set()
            if not self._worker_task or self._worker_task.done():
                self._worker_task = asyncio.create_task(self._worker())
        return t

    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task by id (pending or currently running)"""
        async with self._lock:
            # cancel pending
            for i, t in enumerate(self.pending):
                if t.task_id == task_id:
                    t.cancel()
                    self.completed.insert(0, t)
                    del self.pending[i]
                    return True
            # cancel running
            if self.running and self.running.task_id == task_id:
                self.running.cancel()
                return True
        return False

    def snapshot(self) -> dict[str, Any]:
        """
        Return a shallow copy of the current queue state (running, pending, completed).
        """
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
            adapter = ConfigAdapter(config=self._settings, site=task.site)
            downloader_cfg = adapter.get_downloader_config()
            fetcher_cfg = adapter.get_fetcher_config()
            parser_cfg = adapter.get_parser_config()
            exporter_cfg = adapter.get_exporter_config()
            login_cfg = adapter.get_login_config()

            parser = get_parser(task.site, parser_cfg)
            exporter = get_exporter(task.site, exporter_cfg)

            async with get_fetcher(task.site, fetcher_cfg) as fetcher:
                # login if required
                if downloader_cfg.login_required and not await fetcher.load_state():
                    login_data = await self._prompt_login_fields(
                        task, fetcher.login_fields, login_cfg
                    )
                    if not await fetcher.login(**login_data):
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
                        cancel_event=task._cancel_event,
                    )
                except asyncio.CancelledError:
                    task.status = "cancelled"
                    return

                if task.is_cancelled():
                    task.status = "cancelled"
                    return

                task.exported_paths = await asyncio.to_thread(
                    exporter.export, task.book_id
                )

                if downloader_cfg.login_required and fetcher.is_logged_in:
                    await fetcher.save_state()

                task.status = "completed"

        except Exception as e:
            task.status = "failed"
            task.error = str(e)

    async def _prompt_login_fields(
        self,
        task: DownloadTask,
        fields: list[LoginField],
        login_config: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        """
        Prompt UI login; supports text/password/cookie fields.
        """

        prefill = (login_config or {}).copy()
        req = await create_cred_request(
            task_id=task.task_id,
            title=task.title,
            fields=fields,
            prefill=prefill,
        )

        # wait for UI to submit or cancel
        try:
            await asyncio.wait_for(req.event.wait(), timeout=REQUEST_TIMEOUT)
        except TimeoutError:
            await complete_request(req.req_id, None)
            cleanup_request(req.req_id)
            return prefill

        if task.is_cancelled():
            await complete_request(req.req_id, None)
            cleanup_request(req.req_id)
            return prefill

        # merge values: prefill -> UI (UI wins)
        ui_vals: dict[str, str] = req.result or {}
        cleanup_request(req.req_id)

        merged: dict[str, Any] = {
            k: v.strip() for k, v in prefill.items() if isinstance(v, str)
        }
        merged.update({k: v.strip() for k, v in ui_vals.items() if isinstance(v, str)})

        # parse cookie fields into dicts
        for f in fields:
            if f.type == "cookie":
                raw = merged.get(f.name, "")
                if isinstance(raw, str) and raw:
                    with contextlib.suppress(Exception):
                        # keep raw string if parsing fails
                        merged[f.name] = parse_cookies(raw)

        return merged


manager = TaskManager()
