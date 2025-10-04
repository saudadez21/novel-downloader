#!/usr/bin/env python3
"""
novel_downloader.apps.web.ui_adapters
-------------------------------------
"""

import asyncio
import contextlib
from pathlib import Path
from typing import Any

from novel_downloader.apps.web.models import DownloadTask
from novel_downloader.apps.web.services.cred_broker import (
    REQUEST_TIMEOUT,
    cleanup_request,
    complete_request,
    create_cred_request,
)
from novel_downloader.infra.cookies import parse_cookies
from novel_downloader.schemas import BookConfig, LoginField


class WebLoginUI:
    def __init__(self, task: DownloadTask) -> None:
        self.task = task

    async def prompt(
        self,
        fields: list[LoginField],
        prefill: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        prefill = (prefill or {}).copy()
        req = await create_cred_request(
            task_id=self.task.task_id,
            title=self.task.title,
            fields=fields,
            prefill=prefill,
        )

        try:
            await asyncio.wait_for(req.event.wait(), timeout=REQUEST_TIMEOUT)
        except TimeoutError:
            await complete_request(req.req_id, None)
            cleanup_request(req.req_id)
            return prefill

        if self.task.is_cancelled():
            await complete_request(req.req_id, None)
            cleanup_request(req.req_id)
            return prefill

        ui_vals: dict[str, str] = req.result or {}
        cleanup_request(req.req_id)

        merged: dict[str, Any] = {
            k: v.strip() for k, v in prefill.items() if isinstance(v, str)
        }
        merged.update({k: v.strip() for k, v in ui_vals.items() if isinstance(v, str)})

        # parse cookie fields
        for f in fields:
            if f.type == "cookie":
                raw = merged.get(f.name, "")
                if isinstance(raw, str) and raw:
                    with contextlib.suppress(Exception):
                        merged[f.name] = parse_cookies(raw)

        return merged

    def on_login_failed(self) -> None:
        self.task.status = "failed"
        self.task.error = "登录失败"

    def on_login_success(self) -> None:
        self.task.status = "running"


class WebDownloadUI:
    def __init__(self, task: DownloadTask) -> None:
        self.task = task

    async def on_start(self, book: BookConfig) -> None:
        self.task.status = "running"

    async def on_progress(self, done: int, total: int) -> None:
        self.task.chapters_total = total
        self.task.chapters_done = done
        self.task.record_chapter_time()

    async def on_complete(self, book: BookConfig) -> None:
        self.task.status = "exporting"

    async def on_book_error(self, book: BookConfig, error: Exception) -> None:
        self.task.status = "failed"
        self.task.error = str(error)

    async def on_site_error(self, site: str, error: Exception) -> None:
        self.task.status = "failed"
        self.task.error = str(error)


class WebExportUI:
    def __init__(self, task: DownloadTask) -> None:
        self.task = task
        self.task.exported_paths = {}

    def on_start(self, book: BookConfig, fmt: str | None = None) -> None:
        self.task.status = "exporting"

    def on_success(self, book: BookConfig, fmt: str, path: Path) -> None:
        self.task.exported_paths[fmt] = path

    def on_error(self, book: BookConfig, fmt: str | None, error: Exception) -> None:
        self.task.status = "failed"
        self.task.error = str(error)

    def on_unsupported(self, book: BookConfig, fmt: str) -> None:
        self.task.error = f"Export format '{fmt}' is not supported."


class WebProcessUI:
    def __init__(self, task: DownloadTask) -> None:
        self.task = task

    def on_stage_start(self, book: BookConfig, stage: str) -> None:
        self.task.status = "processing"
        self.task.chapters_done = 0
        self.task._recent_times.clear()

    def on_stage_progress(
        self, book: BookConfig, stage: str, done: int, total: int
    ) -> None:
        self.task.chapters_total = total
        self.task.chapters_done = done
        self.task.record_chapter_time()

    def on_stage_complete(self, book: BookConfig, stage: str) -> None:
        # could store per-stage artifacts later if needed
        pass

    def on_missing(self, book: BookConfig, what: str, path: Path) -> None:
        self.task.status = "failed"
        self.task.error = f"Missing required data ({what}): {path}"

    def on_book_error(
        self, book: BookConfig, stage: str | None, error: Exception
    ) -> None:
        self.task.status = "failed"
        if stage:
            self.task.error = f"Stage '{stage}' error: {error}"
        else:
            self.task.error = str(error)
