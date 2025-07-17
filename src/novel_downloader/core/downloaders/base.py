#!/usr/bin/env python3
"""
novel_downloader.core.downloaders.base
--------------------------------------

Defines the abstract base class `BaseDownloader`, which provides a
common interface and reusable logic for all downloader implementations.
"""

import abc
import json
import logging
from collections.abc import AsyncIterator, Awaitable, Callable, Sequence
from pathlib import Path
from typing import Any

from novel_downloader.core.interfaces import (
    DownloaderProtocol,
    FetcherProtocol,
    ParserProtocol,
)
from novel_downloader.models import BookConfig, DownloaderConfig
from novel_downloader.utils import calculate_time_difference


class BaseDownloader(DownloaderProtocol, abc.ABC):
    """
    Abstract base class for novel downloaders.

    Defines the general interface and batch download workflow,
    while delegating book-specific downloading logic to subclasses.

    Subclasses are required to implement methods for downloading
    a single book, using the provided fetcher and parser components.
    """

    DEFAULT_SOURCE_ID = 0
    DEFAULT_PRIORITIES_MAP = {
        DEFAULT_SOURCE_ID: 0,
    }

    def __init__(
        self,
        fetcher: FetcherProtocol,
        parser: ParserProtocol,
        config: DownloaderConfig,
        site: str,
        priorities: dict[int, int] | None = None,
    ):
        """
        Initialize the downloader for a specific site.

        :param fetcher: Fetcher component for retrieving raw chapter data.
        :param parser: Parser component for extracting chapter content.
        :param config: Downloader configuration settings.
        :param site: Identifier for the target website or source.
        :param priorities: Mapping of source_id to priority value.
                           Lower numbers indicate higher priority.
                           E.X. {0: 10, 1: 100} means source 0 is preferred.
        """
        self._fetcher = fetcher
        self._parser = parser
        self._config = config
        self._site = site
        self._priorities = priorities or self.DEFAULT_PRIORITIES_MAP

        self._raw_data_dir = Path(config.raw_data_dir) / site
        self._raw_data_dir.mkdir(parents=True, exist_ok=True)
        self._debug_dir = Path.cwd() / "debug" / site
        self._debug_dir.mkdir(parents=True, exist_ok=True)

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

    async def load_book_info(
        self,
        book_id: str,
        html_dir: Path,
    ) -> dict[str, Any]:
        book_info = self._load_book_info(
            book_id=book_id,
            max_age_days=1,
        )
        if book_info:
            return book_info

        info_html = await self.fetcher.get_book_info(book_id)
        self._save_html_pages(html_dir, "info", info_html)
        book_info = self.parser.parse_book_info(info_html)

        if book_info:
            self._save_book_info(book_id, book_info)
            return book_info

        return self._load_book_info(book_id)

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

    def _load_book_info(
        self,
        book_id: str,
        *,
        max_age_days: int | None = None,
    ) -> dict[str, Any]:
        """
        Attempt to read and parse the book_info.json for a given book_id.

        :param book_id: identifier of the book
        :param max_age_days: if set, only return if 'update_time' is less
        :return: dict of book info if is valid JSON, else empty
        """
        info_path = self._raw_data_dir / book_id / "book_info.json"
        if not info_path.is_file():
            return {}

        try:
            data: dict[str, Any] = json.loads(info_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}

        if max_age_days is not None:
            days, *_ = calculate_time_difference(
                data.get("update_time", ""),
                "UTC+8",
            )
            if days > max_age_days:
                return {}

        return data

    def _save_book_info(
        self,
        book_id: str,
        book_info: dict[str, Any],
    ) -> None:
        """
        Serialize and save the book_info dict as json.

        :param book_id: identifier of the book
        :param book_info: dict containing metadata about the book
        """
        target_dir = self._raw_data_dir / book_id
        target_dir.mkdir(parents=True, exist_ok=True)
        (target_dir / "book_info.json").write_text(
            json.dumps(book_info, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _save_html_pages(
        self,
        html_dir: Path,
        filename: str,
        html_list: Sequence[str],
    ) -> None:
        """
        If save_html is enabled, write each HTML snippet to a file.

        Filenames will be {chap_id}_{index}.html in html_dir.

        :param html_dir: directory in which to write HTML files
        :param filename: used as filename prefix
        :param html_list: list of HTML strings to save
        """
        if not self.save_html:
            return

        html_dir.mkdir(parents=True, exist_ok=True)
        for i, html in enumerate(html_list):
            file_path = html_dir / f"{filename}_{i}.html"
            file_path.write_text(html, encoding="utf-8")

    @staticmethod
    async def _chapter_ids(
        volumes: list[dict[str, Any]],
        start_id: str | None,
        end_id: str | None,
    ) -> AsyncIterator[str]:
        """
        Yield each chapterId in order, respecting start/end bounds.
        """
        seen_start = start_id is None
        for vol in volumes:
            for chap in vol.get("chapters", []):
                cid = chap.get("chapterId")
                if not cid:
                    continue
                if not seen_start:
                    if cid == start_id:
                        seen_start = True
                    else:
                        continue
                yield cid
                if end_id is not None and cid == end_id:
                    return

    @property
    def fetcher(self) -> FetcherProtocol:
        return self._fetcher

    @property
    def parser(self) -> ParserProtocol:
        return self._parser

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

    @property
    def storage_batch_size(self) -> int:
        return max(1, self._config.storage_batch_size)

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
