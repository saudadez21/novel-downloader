#!/usr/bin/env python3
"""
novel_downloader.plugins.base.downloader
----------------------------------------

Abstract base class providing common workflow and utilities for novel downloaders
"""

import abc
import asyncio
import json
import logging
import time
from collections.abc import Awaitable, Callable, Sequence
from pathlib import Path
from typing import Any

from novel_downloader.plugins.protocols import FetcherProtocol, ParserProtocol
from novel_downloader.schemas import (
    BookConfig,
    BookInfoDict,
    DownloaderConfig,
)

ONE_DAY = 86400  # seconds


class BaseDownloader(abc.ABC):
    """
    Abstract base class for novel downloaders.

    Defines the general interface and batch download workflow,
    while delegating book-specific downloading logic to subclasses.

    Subclasses are required to implement methods for downloading
    a single book, using the provided fetcher and parser components.
    """

    def __init__(
        self,
        fetcher: FetcherProtocol,
        parser: ParserProtocol,
        config: DownloaderConfig,
        site: str,
    ):
        """
        Initialize the downloader for a specific site.

        :param fetcher: Fetcher component for retrieving raw chapter data.
        :param parser: Parser component for extracting chapter content.
        :param config: Downloader configuration settings.
        :param site: Identifier for the target website or source.
        """
        self._fetcher = fetcher
        self._parser = parser
        self._site = site

        self._save_html = config.save_html
        self._skip_existing = config.skip_existing
        self._login_required = config.login_required
        self._request_interval = config.request_interval
        self._retry_times = config.retry_times
        self._backoff_factor = config.backoff_factor
        self._workers = config.workers
        self._storage_batch_size = max(1, config.storage_batch_size)

        self._raw_data_dir = Path(config.raw_data_dir) / site
        self._debug_dir = Path.cwd() / "debug" / site

        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    async def download(
        self,
        book: BookConfig,
        *,
        progress_hook: Callable[[int, int], Awaitable[None]] | None = None,
        cancel_event: asyncio.Event | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Download a single book with pre-download hook and error handling.

        :param book: BookConfig with at least 'book_id'.
        :param progress_hook: Optional async callback after each chapter.
                                args: completed_count, total_count.
        :param cancel_event: Optional asyncio.Event to allow cancellation.
        """
        if not self._check_login():
            self.logger.warning(
                "%s login failed, skipping download of book: %s (%s-%s)",
                self._site,
                book.book_id,
                book.start_id or "-",
                book.end_id or "-",
            )
            return

        # if already cancelled before starting
        if cancel_event and cancel_event.is_set():
            self.logger.info(
                "%s download cancelled before start of book: %s",
                self._site,
                book.book_id,
            )
            return

        await self._download_one(
            book,
            progress_hook=progress_hook,
            cancel_event=cancel_event,
            **kwargs,
        )

    @abc.abstractmethod
    async def _download_one(
        self,
        book: BookConfig,
        *,
        progress_hook: Callable[[int, int], Awaitable[None]] | None = None,
        cancel_event: asyncio.Event | None = None,
        **kwargs: Any,
    ) -> None:
        """
        Subclasses must implement this to define how to download a single book.
        """
        ...

    async def _load_book_info(self, book_id: str) -> BookInfoDict:
        """
        Attempt to fetch and parse the book_info for a given book_id.

        :param book_id: identifier of the book
        :return: parsed BookInfoDict
        """
        info_path = self._raw_data_dir / book_id / "book_info.raw.json"
        book_info: BookInfoDict | None = None

        if info_path.exists():
            try:
                book_info = json.loads(info_path.read_text(encoding="utf-8"))
                if (
                    book_info
                    and time.time() - book_info.get("last_checked", 0.0) < ONE_DAY
                ):
                    return book_info
            except json.JSONDecodeError:
                self.logger.warning(
                    "Corrupted book_info.raw.json for %s: could not decode JSON",
                    book_id,
                )

        try:
            info_html = await self.fetcher.get_book_info(book_id)
            self._save_html_pages(book_id, "info", info_html)

            book_info = self.parser.parse_book_info(info_html)
            if book_info:
                book_info["last_checked"] = time.time()
                self._save_book_info(book_id, book_info)
                return book_info

        except Exception as exc:
            self.logger.warning(
                "Failed to fetch/parse book_info for %s: %s", book_id, exc
            )

        if book_info is None:
            raise LookupError(f"Unable to load book_info for {book_id}")

        return book_info

    def _save_book_info(self, book_id: str, book_info: BookInfoDict) -> None:
        """
        Serialize and save the book_info dict as json.

        :param book_id: identifier of the book
        :param book_info: dict containing metadata about the book
        """
        target_dir = self._raw_data_dir / book_id
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "book_info.raw.json").write_text(
            json.dumps(book_info, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _save_html_pages(
        self,
        book_id: str,
        filename: str,
        html_list: Sequence[str],
        *,
        folder: str = "html",
    ) -> None:
        """
        If save_html is enabled, write each HTML snippet to a file.

        Filenames will be {book_id}_{filename}_{index}.html in html_dir.

        :param book_id: The book identifier
        :param filename: used as filename prefix
        :param html_list: list of HTML strings to save
        """
        if not self._save_html:
            return
        html_dir = self._debug_dir / folder
        html_dir.mkdir(parents=True, exist_ok=True)
        for i, html in enumerate(html_list):
            (html_dir / f"{book_id}_{filename}_{i}.html").write_text(
                html, encoding="utf-8"
            )

    @property
    def fetcher(self) -> FetcherProtocol:
        return self._fetcher

    @property
    def parser(self) -> ParserProtocol:
        return self._parser

    @property
    def workers(self) -> int:
        return self._workers

    def _check_login(self) -> bool:
        """
        Check login if needed.
        """
        return self.fetcher.is_logged_in if self._login_required else True
