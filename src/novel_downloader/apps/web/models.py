#!/usr/bin/env python3
"""
novel_downloader.apps.web.models
--------------------------------
"""

from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from statistics import fmean
from uuid import uuid4

from novel_downloader.schemas import LoginField


class Status(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    PROCESSING = "processing"
    EXPORTING = "exporting"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


@dataclass
class CredRequest:
    task_id: str
    title: str
    fields: list[LoginField]
    prefill: dict[str, str] = field(default_factory=dict)

    # runtime fields
    req_id: str = field(default_factory=lambda: uuid4().hex)
    event: asyncio.Event = field(default_factory=asyncio.Event, repr=False)
    result: dict[str, str] | None = None

    # claim info (times use time.monotonic() seconds)
    claimed_by: str | None = None
    claimed_at: float | None = None

    # lifecycle
    done: bool = False


@dataclass
class DownloadTask:
    title: str
    site: str
    book_id: str

    # runtime state
    task_id: str = field(default_factory=lambda: uuid4().hex)
    status: Status = Status.QUEUED
    chapters_total: int = 0
    chapters_done: int = 0
    error: str | None = None
    exported_paths: dict[str, Path] = field(default_factory=dict)

    asyncio_task: asyncio.Task[None] | None = field(default=None, repr=False)

    _recent: deque[float] = field(default_factory=lambda: deque(maxlen=20), repr=False)
    _last_ts: float = field(default_factory=time.monotonic, repr=False)

    def progress(self) -> float:
        return (
            0.0
            if self.chapters_total <= 0
            else round(self.chapters_done / self.chapters_total, 2)
        )

    def record_chapter_time(self) -> None:
        """Record elapsed time for one finished chapter."""
        now = time.monotonic()
        dt = now - self._last_ts
        self._last_ts = now
        if 0 < dt < 120:
            self._recent.append(dt)

    def eta(self) -> float | None:
        """Return ETA in seconds if estimable, else None."""
        if self.chapters_total <= 0 or self.chapters_done >= self.chapters_total:
            return None
        if not self._recent:
            return None
        remaining = self.chapters_total - self.chapters_done
        return fmean(self._recent) * remaining
