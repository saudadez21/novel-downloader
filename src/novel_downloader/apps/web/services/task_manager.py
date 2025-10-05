#!/usr/bin/env python3
"""
novel_downloader.apps.web.services.task_manager
-----------------------------------------------

"""

import asyncio
from collections import defaultdict

from novel_downloader.infra.config import ConfigAdapter, load_config
from novel_downloader.schemas import BookConfig
from novel_downloader.usecases.download import download_books
from novel_downloader.usecases.export import export_books
from novel_downloader.usecases.process import process_books

from ..models import DownloadTask
from ..ui_adapters import WebDownloadUI, WebExportUI, WebLoginUI, WebProcessUI


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

        self._process_waiting: list[DownloadTask] = []
        self._process_worker_task: asyncio.Task[None] | None = None

        self._export_waiting: list[DownloadTask] = []
        self._export_worker_task: asyncio.Task[None] | None = None

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
        adapter = self._adapter
        downloader_cfg = adapter.get_downloader_config(task.site)
        fetcher_cfg = adapter.get_fetcher_config(task.site)
        parser_cfg = adapter.get_parser_config(task.site)
        login_cfg = adapter.get_login_config(task.site)

        login_ui = WebLoginUI(task)
        download_ui = WebDownloadUI(task)

        try:
            await download_books(
                site=task.site,
                books=[BookConfig(book_id=task.book_id)],
                downloader_cfg=downloader_cfg,
                fetcher_cfg=fetcher_cfg,
                parser_cfg=parser_cfg,
                login_ui=login_ui,
                download_ui=download_ui,
                login_config=login_cfg,
            )

            if task.is_cancelled():
                task.status = "cancelled"
                return

            pipeline_cfg = adapter.get_pipeline_config(task.site)
            if pipeline_cfg and pipeline_cfg.processors:
                task.status = "processing"
                self._process_waiting.append(task)
                if not self._process_worker_task or self._process_worker_task.done():
                    self._process_worker_task = asyncio.create_task(
                        self._process_worker()
                    )
            else:
                task.status = "exporting"
                self._export_waiting.append(task)
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

    async def _process_worker(self) -> None:
        while self._process_waiting:
            task = self._process_waiting.pop()
            try:
                if task.is_cancelled():
                    task.status = "cancelled"
                    continue

                pipeline_cfg = self._adapter.get_pipeline_config(task.site)
                if not pipeline_cfg or not pipeline_cfg.processors:
                    # nothing to process; forward to export
                    task.status = "exporting"
                    self._export_waiting.append(task)
                    if not self._export_worker_task or self._export_worker_task.done():
                        self._export_worker_task = asyncio.create_task(
                            self._export_worker()
                        )
                    continue

                proc_ui = WebProcessUI(task)
                await asyncio.to_thread(
                    process_books,
                    task.site,
                    [BookConfig(book_id=task.book_id)],
                    pipeline_cfg,
                    proc_ui,
                )

                if task.is_cancelled():
                    task.status = "cancelled"
                    continue

                # Processing done -> hand off to export
                task.status = "exporting"
                self._export_waiting.append(task)
                if not self._export_worker_task or self._export_worker_task.done():
                    self._export_worker_task = asyncio.create_task(
                        self._export_worker()
                    )

            except asyncio.CancelledError:
                task.status = "cancelled"
                break
            except Exception as e:
                task.status = "failed"
                task.error = str(e)

    async def _export_worker(self) -> None:
        """Dedicated worker for synchronous export tasks."""
        while self._export_waiting:
            task = self._export_waiting.pop()
            try:
                if task.is_cancelled():
                    task.status = "cancelled"
                    continue

                exporter_cfg = self._adapter.get_exporter_config(task.site)
                export_ui = WebExportUI(task)
                await asyncio.to_thread(
                    export_books,
                    site=task.site,
                    books=[BookConfig(book_id=task.book_id)],
                    exporter_cfg=exporter_cfg,
                    export_ui=export_ui,
                )

                if task.is_cancelled():
                    task.status = "cancelled"
                    continue

                task.status = "completed"

            except asyncio.CancelledError:
                task.status = "cancelled"
                break
            except Exception as e:
                task.status = "failed"
                task.error = str(e)

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
