#!/usr/bin/env python3
"""
novel_downloader.plugins.protocols.ui
-------------------------------------

Protocol definitions for user-interface callbacks used by clients.

Each UI protocol represents an event sink for user-facing feedback.
Concrete implementations may be CLI, web-based, or GUI frontends.
"""

from pathlib import Path
from typing import Any, Protocol

from novel_downloader.schemas import BookConfig, LoginField


class LoginUI(Protocol):
    """
    Protocol for user interaction during login.
    """

    async def prompt(
        self,
        fields: list[LoginField],
        prefill: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Prompt the user for login fields."""
        ...

    def on_login_failed(self) -> None:
        """Called when login credentials are rejected."""
        ...

    def on_login_success(self) -> None:
        """Called when login succeeds."""
        ...


class DownloadUI(Protocol):
    """
    Protocol for reporting download progress.
    """

    async def on_start(self, book: BookConfig) -> None:
        """Called before a book download begins."""
        ...

    async def on_progress(self, done: int, total: int) -> None:
        """Called periodically to report progress."""
        ...

    async def on_complete(self, book: BookConfig) -> None:
        """Called when a book download completes."""
        ...


class ExportUI(Protocol):
    """
    Protocol for reporting export progress and results.
    """

    def on_start(self, book: BookConfig, fmt: str | None = None) -> None:
        """Called before export starts."""
        ...

    def on_success(self, book: BookConfig, fmt: str, path: Path) -> None:
        """Called when export succeeds."""
        ...

    def on_error(self, book: BookConfig, fmt: str | None, error: Exception) -> None:
        """Called when an error occurs during export."""
        ...

    def on_unsupported(self, book: BookConfig, fmt: str) -> None:
        """Called when a requested export format is unsupported."""
        ...


class ProcessUI(Protocol):
    """
    Protocol for reporting progress during book processing.
    """

    def on_stage_start(self, book: BookConfig, stage: str) -> None:
        """Called when a processing stage begins."""
        ...

    def on_stage_progress(
        self, book: BookConfig, stage: str, done: int, total: int
    ) -> None:
        """Called to report progress within a processing stage."""
        ...

    def on_stage_complete(self, book: BookConfig, stage: str) -> None:
        """Called when a processing stage completes."""
        ...

    def on_missing(self, book: BookConfig, what: str, path: Path) -> None:
        """Called when an expected file or resource is missing."""
        ...
