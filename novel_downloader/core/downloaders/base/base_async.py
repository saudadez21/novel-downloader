#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.base.base_async
-------------------------------------------------

Defines the abstract base class `BaseAsyncDownloader`, which provides a
common interface and reusable logic for all downloader implementations.
"""

import abc
import logging
from pathlib import Path

from novel_downloader.config import DownloaderConfig
from novel_downloader.core.interfaces import (
    AsyncDownloaderProtocol,
    AsyncRequesterProtocol,
    ParserProtocol,
    SaverProtocol,
)


class BaseAsyncDownloader(AsyncDownloaderProtocol, abc.ABC):
    """
    Abstract downloader that defines the initialization interface
    and the general batch download flow.

    Subclasses must implement the logic for downloading a single book.
    """

    def __init__(
        self,
        requester: AsyncRequesterProtocol,
        parser: ParserProtocol,
        saver: SaverProtocol,
        config: DownloaderConfig,
        site: str,
    ):
        self._requester = requester
        self._parser = parser
        self._saver = saver
        self._config = config
        self._site = site

        self._raw_data_dir = Path(config.raw_data_dir) / site
        self._cache_dir = Path(config.cache_dir) / site
        self._raw_data_dir.mkdir(parents=True, exist_ok=True)
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def download(self, book_ids: list[str]) -> None:
        """
        The general batch download process:
          1. Iterate over all book IDs
          2. For each ID, call `download_one()`

        :param book_ids: A list of book identifiers to download.
        """
        await self.prepare()

        # 2) batch download
        for idx, book_id in enumerate(book_ids, start=1):
            self.logger.debug(
                "[%s] Starting download for %r (%s/%s)",
                self.__class__.__name__,
                book_id,
                idx,
                len(book_ids),
            )
            try:
                await self.download_one(book_id)
            except Exception as e:
                self._handle_download_exception(book_id, e)

    @abc.abstractmethod
    async def download_one(self, book_id: str) -> None:
        """
        The full download logic for a single book.

        Subclasses must implement this method.

        :param book_id: The identifier of the book to download.
        """
        ...

    async def prepare(self) -> None:
        """
        Optional hook called before downloading each book.

        Subclasses can override this method to perform pre-download setup.
        """
        return

    @property
    def requester(self) -> AsyncRequesterProtocol:
        return self._requester

    @property
    def parser(self) -> ParserProtocol:
        return self._parser

    @property
    def saver(self) -> SaverProtocol:
        return self._saver

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
