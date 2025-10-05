#!/usr/bin/env python3
"""
novel_downloader.usecases.protocols
-----------------------------------
"""

from pathlib import Path
from typing import Any, Protocol

from novel_downloader.schemas import BookConfig, LoginField


class LoginUI(Protocol):
    async def prompt(
        self,
        fields: list[LoginField],
        prefill: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Prompt user for login fields. May use CLI, Web form, or other UI.
        """
        ...

    def on_login_failed(self) -> None:
        """
        Called when login credentials are rejected.
        """
        ...

    def on_login_success(self) -> None:
        """
        Called when login succeeds.
        """
        ...


class DownloadUI(Protocol):
    async def on_start(self, book: BookConfig) -> None:
        ...

    async def on_progress(self, done: int, total: int) -> None:
        ...

    async def on_complete(self, book: BookConfig) -> None:
        ...

    async def on_book_error(self, book: BookConfig, error: Exception) -> None:
        ...

    async def on_site_error(self, site: str, error: Exception) -> None:
        ...


class ExportUI(Protocol):
    def on_start(self, book: BookConfig, fmt: str | None = None) -> None:
        ...

    def on_success(self, book: BookConfig, fmt: str, path: Path) -> None:
        ...

    def on_error(self, book: BookConfig, fmt: str | None, error: Exception) -> None:
        ...

    def on_unsupported(self, book: BookConfig, fmt: str) -> None:
        ...


class ConfigUI(Protocol):
    def on_missing(self, path: Path) -> None:
        ...

    def on_created(self, path: Path) -> None:
        ...

    def on_invalid(self, error: Exception) -> None:
        ...

    def on_abort(self) -> None:
        ...

    def confirm_create(self) -> bool:
        ...


class ProcessUI(Protocol):
    def on_stage_start(self, book: BookConfig, stage: str) -> None:
        ...

    def on_stage_progress(
        self, book: BookConfig, stage: str, done: int, total: int
    ) -> None:
        ...

    def on_stage_complete(self, book: BookConfig, stage: str) -> None:
        ...

    def on_missing(self, book: BookConfig, what: str, path: Path) -> None:
        ...

    def on_book_error(
        self, book: BookConfig, stage: str | None, error: Exception
    ) -> None:
        ...
