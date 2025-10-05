#!/usr/bin/env python3
"""
novel_downloader.apps.web.models
--------------------------------
"""

import asyncio
import time
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal
from uuid import uuid4

from novel_downloader.schemas import LoginField

Status = Literal[
    "queued", "running", "processing", "exporting", "completed", "cancelled", "failed"
]


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
    status: Status = "queued"
    chapters_total: int = 0
    chapters_done: int = 0
    error: str | None = None
    exported_paths: dict[str, Path] = field(default_factory=dict)

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
