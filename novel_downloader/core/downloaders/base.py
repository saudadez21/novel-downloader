#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.base
--------------------------------------

Defines the abstract base class `BaseDownloader`, which provides a
common interface and reusable logic for all downloader implementations.
"""

import abc
import logging
from pathlib import Path

from novel_downloader.core.interfaces import (
    DownloaderProtocol,
    ExporterProtocol,
    FetcherProtocol,
    ParserProtocol,
)
from novel_downloader.models import DownloaderConfig


class BaseDownloader(DownloaderProtocol, abc.ABC):
    """
    Abstract downloader that defines the initialization interface
    and the general batch download flow.

    Subclasses must implement the logic for downloading a single book.
    """

    def __init__(
        self,
        fetcher: FetcherProtocol,
        parser: ParserProtocol,
        exporter: ExporterProtocol,
        config: DownloaderConfig,
        site: str,
    ):
        self._fetcher = fetcher
        self._parser = parser
        self._exporter = exporter
        self._config = config
        self._site = site

        self._raw_data_dir = Path(config.raw_data_dir) / site
        self._cache_dir = Path(config.cache_dir) / site
        self._raw_data_dir.mkdir(parents=True, exist_ok=True)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    async def download_many(self, book_ids: list[str]) -> None:
        """
        Download multiple books with pre-download hook and error handling.

        :param book_ids: A list of book identifiers to download.
        """
        if not await self._ensure_ready():
            self.logger.warning(
                "[%s] login failed, skipping download of %s",
                self._site,
                book_ids,
            )
            return

        for book_id in book_ids:
            try:
                await self._download_one(book_id)
            except Exception as e:
                self._handle_download_exception(book_id, e)

        await self._finalize()

    async def download(self, book_id: str) -> None:
        """
        Download a single book with pre-download hook and error handling.

        :param book_id: The identifier of the book to download.
        """
        if not await self._ensure_ready():
            self.logger.warning(
                "[%s] login failed, skipping download of %s",
                self._site,
                book_id,
            )
            return

        try:
            await self._download_one(book_id)
        except Exception as e:
            self._handle_download_exception(book_id, e)

        await self._finalize()

    @abc.abstractmethod
    async def _download_one(self, book_id: str) -> None:
        """
        Subclasses must implement this to define how to download a single book.
        """
        ...

    async def _prepare(self) -> None:
        """
        Optional hook called before downloading.

        Subclasses can override this method to perform pre-download setup.
        """
        return

    async def _finalize(self) -> None:
        """
        Optional hook called after downloading is complete.

        Subclasses can override this method to perform post-download tasks,
        such as saving state or releasing resources.
        """
        return

    @property
    def fetcher(self) -> FetcherProtocol:
        return self._fetcher

    @property
    def parser(self) -> ParserProtocol:
        return self._parser

    @property
    def exporter(self) -> ExporterProtocol:
        return self._exporter

    @property
    def config(self) -> DownloaderConfig:
        return self._config

    @property
    def raw_data_dir(self) -> Path:
        return self._raw_data_dir

    @property
    def cache_dir(self) -> Path:
        return self._cache_dir

    @property
    def site(self) -> str:
        return self._site

    @property
    def save_html(self) -> bool:
        return self._config.save_html

    @property
    def skip_existing(self) -> bool:
        return self._config.skip_existing

    @property
    def login_required(self) -> bool:
        return self._config.login_required

    @property
    def request_interval(self) -> float:
        return self._config.request_interval

    @property
    def retry_times(self) -> int:
        return self._config.retry_times

    @property
    def backoff_factor(self) -> float:
        return self._config.backoff_factor

    @property
    def parser_workers(self) -> int:
        return self._config.parser_workers

    @property
    def download_workers(self) -> int:
        return self._config.download_workers

    def _handle_download_exception(self, book_id: str, error: Exception) -> None:
        """
        Handle download errors in a consistent way.

        This method can be overridden or extended to implement retry logic, etc.

        :param book_id: The ID of the book that failed.
        :param error: The exception raised during download.
        """
        self.logger.warning(
            "[%s] Failed to download %r: %s",
            self.__class__.__name__,
            book_id,
            error,
        )

    async def _ensure_ready(self) -> bool:
        """
        Run pre-download preparation and check login if needed.
        """
        await self._prepare()

        return self.fetcher.is_logged_in if self.login_required else True
