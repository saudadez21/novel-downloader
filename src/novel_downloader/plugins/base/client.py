#!/usr/bin/env python3
"""
novel_downloader.plugins.base.client
------------------------------------

Abstract base class providing common
"""

import abc
import logging
import types
from pathlib import Path
from typing import Any, Self

from novel_downloader.plugins.protocols import FetcherProtocol, ParserProtocol
from novel_downloader.plugins.protocols.ui import (
    DownloadUI,
    ExportUI,
    LoginUI,
    ProcessUI,
)
from novel_downloader.plugins.registry import registrar
from novel_downloader.schemas import (
    BookConfig,
    ClientConfig,
    ExporterConfig,
    FetcherConfig,
    ParserConfig,
    ProcessorConfig,
)


class BaseClient(abc.ABC):
    """
    Abstract base class for site client.
    """

    def __init__(
        self,
        site: str,
        config: ClientConfig | None = None,
    ) -> None:
        """
        Initialize the downloader for a specific site.

        :param site: Identifier for the target website or source.
        :param config: Downloader configuration settings.
        """
        self._site = site
        cfg = config or ClientConfig()

        self._save_html = cfg.save_html
        self._skip_existing = cfg.skip_existing
        self._request_interval = cfg.request_interval
        self._retry_times = cfg.retry_times
        self._backoff_factor = cfg.backoff_factor
        self._workers = max(1, cfg.workers)
        self._storage_batch_size = max(1, cfg.storage_batch_size)

        self._fetcher_cfg = cfg.fetcher_cfg
        self._parser_cfg = cfg.parser_cfg

        self._fetcher: FetcherProtocol | None = None
        self._parser: ParserProtocol | None = None

        self._raw_data_dir = Path(cfg.raw_data_dir) / site
        self._output_dir = Path(cfg.output_dir)
        self._debug_dir = Path.cwd() / "debug" / site

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def init(self, fetcher_cfg: FetcherConfig, parser_cfg: ParserConfig) -> None:
        if self._fetcher or self._parser:
            await self.close()
        self._fetcher = registrar.get_fetcher(self._site, fetcher_cfg)
        self._parser = registrar.get_parser(self._site, parser_cfg)

        await self._fetcher.init()

    async def close(self) -> None:
        if self._fetcher:
            if self._fetcher.is_logged_in:
                await self._fetcher.save_state()
            await self._fetcher.close()
            self._fetcher = None
        self._parser = None

    @abc.abstractmethod
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

    @abc.abstractmethod
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

    @abc.abstractmethod
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

    @abc.abstractmethod
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

    @abc.abstractmethod
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

    @property
    def fetcher(self) -> FetcherProtocol:
        """
        Return the active fetcher.

        :raises RuntimeError: If the fetcher is uninitialized.
        """
        if self._fetcher is None:
            raise RuntimeError("Fetcher is not initialized.")
        return self._fetcher

    @property
    def parser(self) -> ParserProtocol:
        """
        Return the active parser.

        :raises RuntimeError: If the parser is uninitialized.
        """
        if self._parser is None:
            raise RuntimeError("Fetcher is not initialized.")
        return self._parser

    @property
    def workers(self) -> int:
        return self._workers

    async def __aenter__(self) -> Self:
        await self.init(self._fetcher_cfg, self._parser_cfg)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        tb: types.TracebackType | None,
    ) -> None:
        await self.close()
