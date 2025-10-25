#!/usr/bin/env python3
"""
novel_downloader.apps.web.services.task_manager
-----------------------------------------------

"""

import asyncio
from collections import defaultdict, deque
from collections.abc import Callable, Coroutine
from typing import Any

from novel_downloader.infra.config import ConfigAdapter, load_config
from novel_downloader.plugins import ClientProtocol, registrar
from novel_downloader.schemas import BookConfig

from ..models import DownloadTask, Status
from ..ui_adapters import WebDownloadUI, WebExportUI, WebLoginUI, WebProcessUI

MAX_COMPLETED_TASKS = 100


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
        self.completed: deque[DownloadTask] = deque(maxlen=MAX_COMPLETED_TASKS)

        self._worker_tasks: dict[str, asyncio.Task[None]] = {}

        self._process_waiting: asyncio.Queue[DownloadTask] = asyncio.Queue()
        self._export_waiting: asyncio.Queue[DownloadTask] = asyncio.Queue()

        self._process_worker_task: asyncio.Task[None] | None = None
        self._export_worker_task: asyncio.Task[None] | None = None

        self._clients: dict[str, ClientProtocol] = {}

        self._lock = asyncio.Lock()
        self._adapter = ConfigAdapter(load_config())

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
            for queue in self.pending.values():
                for i, pending_task in enumerate(queue):
                    if pending_task.task_id == task_id:
                        pending_task.status = Status.CANCELLED
                        self.completed.append(pending_task)
                        queue.pop(i)
                        return True

            # cancel running
            for running_task in self.running.values():
                if running_task.task_id == task_id:
                    if running_task.asyncio_task:
                        running_task.asyncio_task.cancel()
                    running_task.status = Status.CANCELLED
                    return True
        return False

    def snapshot(self) -> dict[str, list[DownloadTask]]:
        """
        Return a shallow copy of the current queue state (running, pending, completed).
        """
        return {
            "running": list(self.running.values()),
            "pending": [task_item for q in self.pending.values() for task_item in q],
            "completed": list(self.completed),
        }

    async def close(self) -> None:
        """Cancel or gracefully finish all workers before shutdown."""
        all_tasks = [*self._worker_tasks.values()]
        if self._export_worker_task:
            all_tasks.append(self._export_worker_task)
        if self._process_worker_task:
            all_tasks.append(self._process_worker_task)

        for worker_task in all_tasks:
            worker_task.cancel()

        results = await asyncio.gather(*all_tasks, return_exceptions=True)
        for result in results:
            if isinstance(result, Exception) and not isinstance(
                result, asyncio.CancelledError
            ):
                print(f"Worker error during shutdown: {result!r}")

        self._worker_tasks.clear()
        self._export_worker_task = self._process_worker_task = None

    # ---------- internals ----------
    def _get_client(self, site: str) -> ClientProtocol:
        """Get or create a client instance for a site."""
        if site not in self._clients:
            self._clients[site] = registrar.get_client(
                site, self._adapter.get_client_config(site)
            )

        return self._clients[site]

    def _ensure_worker(
        self, name: str, worker_fn: Callable[[], Coroutine[Any, Any, None]]
    ) -> None:
        """Ensure a background worker is running."""
        worker_task = getattr(self, name)
        if not worker_task or worker_task.done():
            setattr(self, name, asyncio.create_task(worker_fn()))

    def _queue_for_export(self, task: DownloadTask) -> None:
        """Enqueue a task for export and start the export worker if needed."""
        task.status = Status.EXPORTING
        self._export_waiting.put_nowait(task)
        self._ensure_worker("_export_worker_task", self._export_worker)

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
                current_task = self.pending[site].pop(0)
                self.running[site] = current_task

            try:
                await self._run_task(current_task)
            except asyncio.CancelledError:
                current_task.status = Status.CANCELLED
                current_task.error = "Cancelled by user"
            except Exception as e:
                current_task.status = Status.FAILED
                current_task.error = str(e)
            finally:
                async with self._lock:
                    self.completed.append(current_task)
                    self.running.pop(site, None)

    async def _run_task(self, task: DownloadTask) -> None:
        """Run a single download task and dispatch to processing or export."""
        task.status = Status.RUNNING
        adapter = self._adapter
        client = self._get_client(task.site)

        login_ui = WebLoginUI(task)
        download_ui = WebDownloadUI(task)

        async def download_books() -> None:
            async with client:
                if adapter.get_login_required(task.site):
                    success = await client.login(
                        ui=login_ui, login_cfg=adapter.get_login_config(task.site)
                    )
                    if not success:
                        return
                await client.download(BookConfig(book_id=task.book_id), ui=download_ui)

        task.asyncio_task = asyncio.create_task(download_books())
        await task.asyncio_task

        pipeline_cfg = adapter.get_pipeline_config(task.site)
        if pipeline_cfg and pipeline_cfg.processors:
            task.status = Status.PROCESSING
            await self._process_waiting.put(task)
            self._ensure_worker("_process_worker_task", self._process_worker)
        else:
            self._queue_for_export(task)

    async def _process_worker(self) -> None:
        """Worker to run synchronous processing tasks sequentially."""
        while True:
            current_task = await self._process_waiting.get()
            if current_task.status == Status.CANCELLED:
                self._process_waiting.task_done()
                continue
            try:
                client = self._get_client(current_task.site)
                processors = self._adapter.get_processor_configs(current_task.site)
                if not processors:
                    self._queue_for_export(current_task)
                    continue

                await asyncio.to_thread(
                    client.process,
                    BookConfig(book_id=current_task.book_id),
                    processors=processors,
                    ui=WebProcessUI(current_task),
                )
                self._queue_for_export(current_task)

            except asyncio.CancelledError:
                current_task.status = Status.CANCELLED
                break
            except Exception as e:
                current_task.status = Status.FAILED
                current_task.error = str(e)
            finally:
                self._process_waiting.task_done()

    async def _export_worker(self) -> None:
        """Dedicated worker for synchronous export tasks."""
        while True:
            current_task = await self._export_waiting.get()
            if current_task.status == Status.CANCELLED:
                self._export_waiting.task_done()
                continue
            try:
                client = self._get_client(current_task.site)
                await asyncio.to_thread(
                    client.export,
                    BookConfig(book_id=current_task.book_id),
                    cfg=self._adapter.get_exporter_config(current_task.site),
                    ui=WebExportUI(current_task),
                )
                current_task.status = Status.COMPLETED
            except asyncio.CancelledError:
                current_task.status = Status.CANCELLED
                break
            except Exception as e:
                current_task.status = Status.FAILED
                current_task.error = str(e)
            finally:
                self._export_waiting.task_done()


manager = TaskManager()
