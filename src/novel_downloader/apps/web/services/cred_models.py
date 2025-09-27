#!/usr/bin/env python3
"""
novel_downloader.apps.web.services.cred_models
----------------------------------------------

Lightweight data models for the credential broker
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from uuid import uuid4

from novel_downloader.schemas import LoginField


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
