#!/usr/bin/env python3
"""
novel_downloader.plugins.protocols.client
-----------------------------------------

Protocol defining the interface for client implementations
"""

import types
from pathlib import Path
from typing import Any, Protocol, Self

from novel_downloader.schemas import (
    BookConfig,
    ExporterConfig,
    FetcherConfig,
    ParserConfig,
    ProcessorConfig,
)

from .ui import (
    DownloadUI,
    ExportUI,
    LoginUI,
    ProcessUI,
)


class ClientProtocol(Protocol):
    """
    Protocol for a book client implementation.

    Defines the core interface for downloading, processing, exporting,
    and managing book-related resources.
    """

    async def init(self, fetcher_cfg: FetcherConfig, parser_cfg: ParserConfig) -> None:
        ...

    async def close(self) -> None:
        ...

    async def login(
        self,
        *,
        ui: LoginUI,
        login_cfg: dict[str, str] | None = None,
        **kwargs: Any,
    ) -> bool:
        """
        Attempt to log in asynchronously.

        :returns: True if login succeeded.
        """
        ...

    async def download(
        self,
        book: BookConfig,
        *,
        ui: DownloadUI | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Download a single book.

        :param book: BookConfig with at least 'book_id'.
        :param cancel_event: Optional asyncio.Event to allow cancellation.
        :param ui: Optional DownloadUI to report progress or messages.
        """
        ...

    def process(
        self,
        book: BookConfig,
        processors: list[ProcessorConfig],
        *,
        ui: ProcessUI | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Run all processors for a single book.

        :param book: BookConfig to process.
        :param ui: Optional ProcessUI to report progress.
        """
        ...

    async def cache_images(
        self,
        book: BookConfig,
        *,
        force_update: bool = False,
        concurrent: int = 10,
        **kwargs: Any,
    ) -> None:
        """
        Asynchronously pre-cache all images associated with a book.

        :param book: The BookConfig instance representing the book.
        :param force_update: If True, re-download even if images are already cached.
        :param concurrent: Maximum number of concurrent download tasks.
        """
        ...

    def export(
        self,
        book: BookConfig,
        cfg: ExporterConfig | None = None,
        *,
        formats: list[str] | None = None,
        stage: str | None = None,
        ui: ExportUI | None = None,
        **kwargs: Any,
    ) -> dict[str, list[Path]]:
        """
        Persist the assembled book to disk.

        :param book: The book configuration to export.
        :param cfg: Optional ExporterConfig defining export parameters.
        :param formats: Optional list of format strings (e.g., ['epub', 'txt']).
        :param ui: Optional ExportUI for reporting export progress.
        :return: A mapping from format name to the resulting file path.
        """
        ...

    async def __aenter__(self) -> Self:
        ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        tb: types.TracebackType | None,
    ) -> None:
        ...
