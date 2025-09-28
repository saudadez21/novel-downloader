#!/usr/bin/env python3
"""
novel_downloader.apps.web.services.task_manager
-----------------------------------------------

"""

import asyncio
import contextlib
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal
from uuid import uuid4

from novel_downloader.infra.config import ConfigAdapter, load_config
from novel_downloader.infra.cookies import parse_cookies
from novel_downloader.plugins import registrar
from novel_downloader.schemas import (
    BookConfig,
    ExporterConfig,
    LoginField,
)

from .cred_broker import (
    REQUEST_TIMEOUT,
    cleanup_request,
    complete_request,
    create_cred_request,
)

Status = Literal["queued", "running", "exporting", "completed", "cancelled", "failed"]


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

    _recent_times: deque[float] = field(
        default_factory=lambda: deque(maxlen=20), repr=False
    )
    _last_timestamp: float = field(default_factory=time.monotonic, repr=False)

    def progress(self) -> float:
        if self.chapters_total <= 0:
            return 0.0
        return round(self.chapters_done / self.chapters_total, 2)

    def record_chapter_time(self) -> None:
        """Record elapsed time for one finished chapter."""
        now = time.monotonic()
        elapsed = now - self._last_timestamp
        self._last_timestamp = now
        if elapsed > 0:
            self._recent_times.append(elapsed)

    def eta(self) -> float | None:
        """Return ETA in seconds if estimable, else None."""
        if self.chapters_total <= 0 or self.chapters_done >= self.chapters_total:
            return None
        if not self._recent_times:
            return None
        avg = sum(self._recent_times) / len(self._recent_times)
        remaining = self.chapters_total - self.chapters_done
        return avg * remaining

    def cancel(self) -> None:
        self._cancel_event.set()
        self.status = "cancelled"

    def is_cancelled(self) -> bool:
        return self._cancel_event.is_set()


class TaskManager:
    """
    A multi-site task manager:
      * Each site has its own queue and a single worker.
      * Tasks from the same site run sequentially.
      * Tasks from different sites can run in parallel.
      * Workers automatically exit when their site's queue becomes empty.
      * A dedicated export worker runs synchronous export tasks sequentially.
    """

    def __init__(self) -> None:
        self.pending: dict[str, list[DownloadTask]] = defaultdict(list)
        self.running: dict[str, DownloadTask] = {}
        self.completed: list[DownloadTask] = []

        self._worker_tasks: dict[str, asyncio.Task[None]] = {}
        self._export_waiting: list[tuple[DownloadTask, ExporterConfig]] = []
        self._export_worker_task: asyncio.Task[None] | None = None

        self._lock = asyncio.Lock()
        self._settings = load_config()

    # ---------- public API ----------
    async def add_task(self, *, title: str, site: str, book_id: str) -> DownloadTask:
        """
        Add a new task and ensure a worker for its site is running.
        """
        task = DownloadTask(title=title, site=site, book_id=book_id)
        async with self._lock:
            self.pending[site].append(task)
            # start a new worker if needed
            if site not in self._worker_tasks or self._worker_tasks[site].done():
                self._worker_tasks[site] = asyncio.create_task(self._site_worker(site))
        return task

    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a task by id (either pending or currently running).
        """
        async with self._lock:
            # cancel pending
            for _, queue in self.pending.items():
                for i, pending_task in enumerate(queue):
                    if pending_task.task_id == task_id:
                        pending_task.cancel()
                        self.completed.insert(0, pending_task)
                        del queue[i]
                        return True
            # cancel running
            for _, running_task in self.running.items():
                if running_task and running_task.task_id == task_id:
                    running_task.cancel()
                    return True
        return False

    def snapshot(self) -> dict[str, list[DownloadTask]]:
        """
        Return a shallow copy of the current queue state (running, pending, completed).
        """
        return {
            "running": [t for t in self.running.values() if t],
            "pending": [t for q in self.pending.values() for t in q],
            "completed": list(self.completed),
        }

    # ---------- internals ----------
    async def _site_worker(self, site: str) -> None:
        """
        Sequentially run tasks for a specific site until its queue is empty.
        """
        while True:
            async with self._lock:
                if not self.pending[site]:
                    self.running.pop(site, None)
                    self._worker_tasks.pop(site, None)
                    return
                task = self.pending[site].pop(0)
                self.running[site] = task

            await self._run_task(task)

            async with self._lock:
                self.completed.insert(0, task)
                self.running.pop(site, None)

    async def _run_task(self, task: DownloadTask) -> None:
        task.status = "running"
        adapter = ConfigAdapter(config=self._settings, site=task.site)
        downloader_cfg = adapter.get_downloader_config()
        fetcher_cfg = adapter.get_fetcher_config()
        parser_cfg = adapter.get_parser_config()
        exporter_cfg = adapter.get_exporter_config()
        login_cfg = adapter.get_login_config()

        parser = registrar.get_parser(task.site, parser_cfg)

        try:
            async with registrar.get_fetcher(task.site, fetcher_cfg) as fetcher:
                if downloader_cfg.login_required and not await fetcher.load_state():
                    login_data = await self._prompt_login_fields(
                        task, fetcher.login_fields, login_cfg
                    )
                    if not await fetcher.login(**login_data):
                        task.status = "failed"
                        task.error = "登录失败或已取消"
                        return
                    await fetcher.save_state()

                downloader = registrar.get_downloader(
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
                    if done > task.chapters_done:
                        task.record_chapter_time()
                    task.chapters_done = done

                book_cfg: BookConfig = {"book_id": task.book_id}
                await downloader.download(
                    book_cfg,
                    progress_hook=_progress_hook,
                    cancel_event=task._cancel_event,
                )

                if task.is_cancelled():
                    task.status = "cancelled"
                    return

                task.status = "exporting"
                self._export_waiting.append((task, exporter_cfg))
                if not self._export_worker_task or self._export_worker_task.done():
                    self._export_worker_task = asyncio.create_task(
                        self._export_worker()
                    )

        except asyncio.CancelledError:
            task.status = "cancelled"
            raise
        except Exception as e:
            task.status = "failed"
            task.error = str(e)

    async def _export_worker(self) -> None:
        """Dedicated worker for synchronous export tasks."""
        while self._export_waiting:
            task, exporter_cfg = self._export_waiting.pop()
            exporter = registrar.get_exporter(task.site, exporter_cfg)
            try:
                if task.is_cancelled():
                    task.status = "cancelled"
                    continue
                book_cfg: BookConfig = {"book_id": task.book_id}
                task.exported_paths = await asyncio.to_thread(exporter.export, book_cfg)
                task.status = "completed"
            except asyncio.CancelledError:
                task.status = "cancelled"
                break
            except Exception as e:
                task.status = "failed"
                task.error = str(e)
            finally:
                with contextlib.suppress(Exception):
                    exporter.close()

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

    async def close(self) -> None:
        """Cancel or gracefully finish all workers before shutdown."""
        tasks = [t for t in self._worker_tasks.values() if not t.done()]
        if self._export_worker_task and not self._export_worker_task.done():
            tasks.append(self._export_worker_task)

        for t in tasks:
            t.cancel()

        self._worker_tasks.clear()
        self._export_worker_task = None

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for r in results:
                if isinstance(r, Exception) and not isinstance(
                    r, asyncio.CancelledError
                ):
                    print(f"Worker error during shutdown: {r!r}")


manager = TaskManager()
