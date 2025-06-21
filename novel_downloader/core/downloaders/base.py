#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.base
--------------------------------------

Defines the abstract base class `BaseDownloader`, which provides a
common interface and reusable logic for all downloader implementations.
"""

import abc
import logging
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from novel_downloader.core.interfaces import (
    DownloaderProtocol,
    FetcherProtocol,
    ParserProtocol,
)
from novel_downloader.models import BookConfig, DownloaderConfig


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
        config: DownloaderConfig,
        site: str,
    ):
        self._fetcher = fetcher
        self._parser = parser
        self._config = config
        self._site = site

        self._raw_data_dir = Path(config.raw_data_dir) / site
        self._cache_dir = Path(config.cache_dir) / site
        self._raw_data_dir.mkdir(parents=True, exist_ok=True)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(f"{self.__class__.__name__}")

    async def download_many(
        self,
        books: list[BookConfig],
        *,
        progress_hook: Callable[[int, int], Awaitable[None]] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Download multiple books with pre-download hook and error handling.

        :param books: List of BookConfig entries.
        :param progress_hook: Optional async callback after each chapter.
                                args: completed_count, total_count.
        """
        if not await self._ensure_ready():
            book_ids = [b["book_id"] for b in books]
            self.logger.warning(
                "[%s] login failed, skipping download of books: %s",
                self._site,
                ", ".join(book_ids) or "<none>",
            )
            return

        for book in books:
            try:
                await self._download_one(
                    book,
                    progress_hook=progress_hook,
                    **kwargs,
                )
            except Exception as e:
                self._handle_download_exception(book, e)

        await self._finalize()

    async def download(
        self,
        book: BookConfig,
        *,
        progress_hook: Callable[[int, int], Awaitable[None]] | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Download a single book with pre-download hook and error handling.

        :param book: BookConfig with at least 'book_id'.
        :param progress_hook: Optional async callback after each chapter.
                                args: completed_count, total_count.
        """
        if not await self._ensure_ready():
            self.logger.warning(
                "[%s] login failed, skipping download of book: %s (%s-%s)",
                self._site,
                book["book_id"],
                book.get("start_id", "-"),
                book.get("end_id", "-"),
            )

        try:
            await self._download_one(
                book,
                progress_hook=progress_hook,
                **kwargs,
            )
        except Exception as e:
            self._handle_download_exception(book, e)

        await self._finalize()

    @abc.abstractmethod
    async def _download_one(
        self,
        book: BookConfig,
        *,
        progress_hook: Callable[[int, int], Awaitable[None]] | None = None,
        **kwargs: Any,
    ) -> None:
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

    def _handle_download_exception(self, book: BookConfig, error: Exception) -> None:
        """
        Handle download errors in a consistent way.

        This method can be overridden or extended to implement retry logic, etc.

        :param book: The book that failed.
        :param error: The exception raised during download.
        """
        self.logger.warning(
            "[%s] Failed to download (book_id=%s, start=%s, end=%s): %s",
            self.__class__.__name__,
            book.get("book_id", "<unknown>"),
            book.get("start_id", "-"),
            book.get("end_id", "-"),
            error,
        )

    async def _ensure_ready(self) -> bool:
        """
        Run pre-download preparation and check login if needed.
        """
        await self._prepare()

        return self.fetcher.is_logged_in if self.login_required else True
