#!/usr/bin/env python3
"""
novel_downloader.schemas.process
--------------------------------
"""

from typing import TypedDict


class ExecutedStageMeta(TypedDict):
    file: str
    processed_at: str  # ISO 8601 timestamp
    depends_on: list[str]
    config_hash: str


class PipelineMeta(TypedDict):
    pipeline: list[str]
    executed: dict[str, ExecutedStageMeta]
